from fastapi import Depends, FastAPI, HTTPException, Request, Response, status, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.repository import (
    add_error,
    add_submission,
    add_student,
    is_student_submission_uploads_limit_reached,
    previous_submission_file_name,
    SessionLocal,
    submission_by_verification_code,
    student_by_nickname,
    student_by_upload_code,
    student_list_summary,
    student_submission_uploads_available,
)
from src.logger import logger
from src.settings import Settings
from src.web.schemas.upload_completion import UploadCompletion
from src.web.schemas.student import Student, StudentCreate
from src.web.schemas.students_submissions_list import StudentsSubmissionsList
from src.web.storage.s3 import s3_shared_instance

app = FastAPI(title=Settings.app_name, description=Settings.app_description, version=Settings.app_version)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    # in case of exception during the request,
    # this middleware will close the database session
    # to avoid leaving dangling connections
    # and then return a 500 response.
    # It returns response instead to raising an HTTPException to
    # make server continue to work without restart.
    with SessionLocal() as session:
        response = Response("Internal server error", status_code=500)
        request.state.db = session
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(str(e))
        finally:
            return response


# Dependencies


def get_db(request: Request):
    return request.state.db


def get_s3():
    return s3_shared_instance


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if credentials.credentials != Settings.auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")


# Routes


@app.get("/", description="Returns the string 'pong'", response_class=PlainTextResponse)
async def pong():
    return "pong"


@app.get(
    "/auth/token",
    description="Returns the bearer token to be used as a value in Authorization header to access protected routes.",
)
async def bearer_token():
    return {"token": Settings.auth_token}


@app.get(
    "/students",
    dependencies=[Depends(verify_token)],
    description="Returns a summary of students and submissions.",
    responses={401: {"description": "Unauthorized"}},
    response_model=StudentsSubmissionsList,
)
async def students_summary(session=Depends(get_db)):
    return student_list_summary(session)


@app.get(
    "/students/{nickname}",
    dependencies=[Depends(verify_token)],
    description="Returns a student by nickname.",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "Not found"}},
    response_model=Student,
)
async def student(nickname: str, session=Depends(get_db)):
    student = student_by_nickname(session, nickname)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post(
    "/students",
    dependencies=[Depends(verify_token)],
    description="Creates a student.",
    responses={
        401: {"description": "Unauthorized"},
        422: {"description": "Duplicate data"},
    },
    response_model=Student,
    status_code=status.HTTP_201_CREATED,
)
async def create_student(student: StudentCreate, session=Depends(get_db)):
    try:
        student = add_student(session, **student.model_dump())
        return student
    except Exception as e:
        orig_error = getattr(e, "orig", None)
        raise HTTPException(status_code=422, detail=str(orig_error))


@app.post(
    "/submissions/{upload_code}",
    description="Creates a submission.",
    responses={
        404: {"description": "Not found"},
        413: {"description": "Payload too large"},
        422: {"description": "Submissions count limit exceeded"},
        429: {"description": "Too Many Requests"},
        500: {"description": "Submission Storage Error"},
    },
    response_model=UploadCompletion,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    upload_code: str,
    file: UploadFile,
    session=Depends(get_db),
    s3=Depends(get_s3),
):
    class UploadSizeError(ValueError):
        pass

    class NotFoundError(ValueError):
        pass

    class CountLimitError(ValueError):
        pass

    try:
        # Check if we can acceps submissions for the student
        student = student_by_upload_code(session, upload_code)
        if not student:
            raise NotFoundError("No student found with the provided upload_code")

        if is_student_submission_uploads_limit_reached(session, student.id):
            raise CountLimitError("Submissions count limit exceeded")

        # Read the file in chunks to avoid loading large files into memory
        await _read_file_in_chunks(file, UploadSizeError)

        # Upload to S3
        resp = s3.upload_file(file)
        await file.close()  # this removes the temporary file

        resp["md5"] = resp["md5"].replace('"', "")

        attrs = {
            "student_id": student.id,
            "file_name": resp["file_name"],
            "md5": resp["md5"],
            "size_bytes": resp["size_bytes"],
        }

        # Create submission record
        submission = add_submission(session, **attrs)

        # Remove previous submission file from S3
        prev_submission_file_name = previous_submission_file_name(session, student.id)
        if prev_submission_file_name:
            s3.remove_file(prev_submission_file_name)

        uploads_available = student_submission_uploads_available(session, student.id)

        return {
            "has_submission": True,
            "last_submission": submission,
            "uploads_available": uploads_available,
        }
    except UploadSizeError:
        raise HTTPException(status_code=413, detail="Upload size limit exceeded")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CountLimitError as e:
        raise HTTPException(status_code=422, detail=str(e))
    # all exceptions which are not from our packages are from s3
    except Exception as e:
        add_error(session, str(e))
        raise HTTPException(status_code=500, detail="Submission Storage Error")


async def _read_file_in_chunks(file, exception_cls):
    """Read a file in chunks and return its contents.

    It raises an exception of the specified class at the moment
    when the size of the contents of the read file exceeds the maximum allowed size.

    Args:
        file: The file-like object to be read.
        exception_cls: The exception class to raise if the file size exceeds the maximum allowed size.

    Returns:
        The contents of the file as bytes.

    Raises:
        exception_cls: If the file size exceeds the maximum allowed size.
    """
    CHUNK_SIZE = 64 * 1024  # 64KB
    MAX_SIZE = Settings.submission_max_size_bytes

    size = 0
    contents = b""

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            logger.info(f'File "{file.filename}" has been submitted, size: {size}')

            # seek to the beginning of the file so it can be read again by boto3
            await file.seek(0)
            return contents

        size += len(chunk)
        if size > MAX_SIZE:
            raise exception_cls()

        contents += chunk


@app.get(
    "/submissions/{upload_code}",
    description="""
    Returns the last submission's metadata by the upload code and number of uploads left
    for the appropriate student.
    """,
    responses={404: {"description": "Not found"}},
    response_model=UploadCompletion,
)
async def get_submission_metadata(upload_code: str, session=Depends(get_db)):
    student = student_by_upload_code(session, upload_code)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    uploads_available = student_submission_uploads_available(session, student.id)

    return {
        "has_submission": student.last_submission is not None,
        "last_submission": student.last_submission,
        "uploads_available": uploads_available,
    }


@app.get(
    "/verifications/{verification_code}/download_url",
    description="Returns URL to download the submission for verification.",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "Not found"}},
)
async def get_verification_download_url(verification_code: str, session=Depends(get_db), s3=Depends(get_s3)):
    submission = submission_by_verification_code(session, verification_code)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return s3.generate_download_url(submission.file_name)
