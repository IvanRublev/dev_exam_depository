from io import BytesIO
import re

from fastapi.testclient import TestClient

from src.database.repository import last_errors
from src.settings import Settings
from src.web.api import app
from tests.conftest import (
    dump_schemas_student,
    dump_schemas_submission,
    mock_upload_file_success_json,
    mock_upload_file_failure,
    mock_generate_download_url_success,
)

client = TestClient(app)

# Root route


def test_pass_get_pong():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "pong"


# Auth route


def test_pass_get_bearer_token():
    response = client.get("/auth/token")
    assert response.status_code == 200
    assert response.json() == {"token": Settings.auth_token}


# Student route


def test_pass_get_students(auth_header, build_models_student, build_models_submission):
    student1 = build_models_student()
    student2 = build_models_student()
    _submission21 = build_models_submission({"student_id": student2.id})
    _submission22 = build_models_submission({"student_id": student2.id})
    submission23 = build_models_submission({"student_id": student2.id})
    student3 = build_models_student()

    response = client.get("/students", headers=auth_header())

    assert response.status_code == 200

    json = response.json()

    assert json["totals"] == {"total_students": 3, "total_submissions": 1}

    assert json["students"] == [
        {
            "nickname": student1.nickname,
            "first_name": student1.first_name,
            "last_name": student1.last_name,
            "has_submission": False,
            "last_submission": None,
        },
        {
            "nickname": student2.nickname,
            "first_name": student2.first_name,
            "last_name": student2.last_name,
            "has_submission": True,
            "last_submission": {
                "verification_code": submission23.verification_code,
                "created_at": submission23.created_at.isoformat(),
            },
        },
        {
            "nickname": student3.nickname,
            "first_name": student3.first_name,
            "last_name": student3.last_name,
            "has_submission": False,
            "last_submission": None,
        },
    ]


def test_fail_get_students_given_invalid_auth_token(auth_header):
    response = client.get("/students", headers=auth_header("invalid_token"))
    assert response.status_code == 401


def test_pass_students_by_nickname(auth_header, build_models_student):
    student = build_models_student()

    response = client.get(f"/students/{student.nickname}", headers=auth_header())

    assert response.status_code == 200
    assert response.json() == dump_schemas_student(student)


def test_pass_students_by_nickname_has_info_about_last_submission(
    auth_header, build_models_student, build_models_submission
):
    student = build_models_student()
    submission = build_models_submission({"student_id": student.id})

    response = client.get(f"/students/{student.nickname}", headers=auth_header())

    assert response.status_code == 200
    response_json = response.json()

    assert response_json["has_submission"] is True
    assert "last_submission" in response_json
    assert response_json["last_submission"]["verification_code"] == submission.verification_code


def test_fail_students_by_nickname_given_nonexistent_nickname(auth_header):
    response = client.get("/students/invalid_student", headers=auth_header())
    assert response.status_code == 404


def test_fail_get_student_nickname_given_invalid_auth_token(auth_header):
    response = client.get("/students/sample_student", headers=auth_header("ivanlid_token"))
    assert response.status_code == 401


def test_pass_post_students(auth_header, build_json_student):
    json = build_json_student()

    response = client.post(
        "/students",
        headers=auth_header(),
        json=json,
    )

    assert response.status_code == 201
    response_json = response.json()

    assert "id" in response_json

    del response_json["id"]
    del response_json["upload_code"]
    del response_json["has_submission"]
    del response_json["last_submission"]
    del response_json["created_at"]
    assert response_json == json


def test_fail_post_students_given_invalid_auth_token(auth_header, build_json_student):
    json = build_json_student()
    response = client.post(
        "/students",
        headers=auth_header("ivanlid_token"),
        json=json,
    )
    assert response.status_code == 401


def test_fail_post_students_given_duplicate_nickname(auth_header, build_models_student, build_json_student):
    student = build_models_student()
    json = build_json_student({"nickname": student.nickname})

    response = client.post(
        "/students",
        headers=auth_header(),
        json=json,
    )

    assert response.status_code == 422
    assert "duplicate key" in response.json()["detail"]


# Submission route


def test_pass_post_submissions(build_models_student, s3):
    student = build_models_student()

    file = BytesIO(b"some file data")
    file.name = "some_filename.txt"

    mock_upload_file_success_json(s3, {"file_name": file.name})

    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 201

    json = response.json()

    assert json["uploads_available"] == Settings.submissions_per_student_count_limit - 1

    assert "last_submission" in json

    last_submission = json["last_submission"]

    assert "md5" in last_submission
    assert re.match(r"^[a-f0-9]{32}$", last_submission["md5"]), "Invalid MD5 value"

    assert "verification_code" in last_submission
    assert "size_bytes" in last_submission

    # assert that it uploaded file to s3

    assert s3.upload_file.call_args[0][0].filename == file.name

    # assert that it created a submission record

    assert len(student.submissions) == 1
    submission = student.submissions[0]
    assert submission.file_name == file.name
    assert submission.md5 == last_submission["md5"]
    assert submission.size_bytes == last_submission["size_bytes"]
    assert submission.verification_code == last_submission["verification_code"]


def test_pass_post_submissions_given_it_removes_the_previous_one(build_models_student, s3):
    student = build_models_student()

    file = BytesIO(b"some file data")
    file.name = "file.txt"

    # Let's submit once
    mock_upload_file_success_json(s3, {"file_name": "first_uploaded_file.txt"})

    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 201

    # Let's submit twice
    mock_upload_file_success_json(s3, {"file_name": "second_uploaded_file.txt"})

    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 201

    # assert that it removed the frist uploaded file from s3

    assert s3.remove_file.call_args[0][0] == "first_uploaded_file.txt"


def test_fail_post_submissions_given_nonexisting_upload_code(s3):
    file = BytesIO(b"some file data")
    file.name = "some_filename.txt"

    mock_upload_file_success_json(s3, {"file_name": file.name})

    response = client.post(
        "/submissions/nonexisting_upload_code",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 404


def test_fail_post_submissions_given_file_larger_than_3mb(build_models_student, s3):
    student = build_models_student()

    file = BytesIO(b"some file data" * 1000000)
    file.name = "some_filename.txt"

    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 413


def test_fail_post_submissions_given_more_than_5_submissions_per_student(build_models_student, s3):
    student = build_models_student()
    file = BytesIO(b"some file data")
    file.name = "some_filename.txt"

    mock_upload_file_success_json(s3, {"file_name": file.name})

    for _ in range(5):
        response = client.post(
            f"/submissions/{student.upload_code}",
            files={"file": (file.name, file, "application/octet-stream")},
        )

        assert response.status_code == 201

    # The 6th submission should fail
    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 422
    assert "Submissions count limit exceeded" in response.json()["detail"]


def test_fail_post_submissions_given_s3_network_error(db_session, build_models_student, s3):
    student = build_models_student()
    file = BytesIO(b"some file data")
    file.name = "some_filename.txt"

    mock_upload_file_failure(s3, ConnectionError("failed to connect to s3"))

    response = client.post(
        f"/submissions/{student.upload_code}",
        files={"file": (file.name, file, "application/octet-stream")},
    )

    assert response.status_code == 500
    assert "Submission Storage Error" in response.json()["detail"]

    # It should collect the error for further analysis

    errors = last_errors(db_session, 1)
    assert len(errors) == 1

    last_error = errors[0]
    assert last_error.detail == "failed to connect to s3"


# Submission route - current state


def test_pass_get_submissions_by_verification_code(build_models_student, build_models_submission):
    student = build_models_student()
    submission = build_models_submission({"student_id": student.id})

    response = client.get(f"/submissions/{student.upload_code}")

    assert response.status_code == 200
    json = response.json()

    submission_fields = dump_schemas_submission(submission)
    del submission_fields["file_name"]

    assert json["has_submission"] is True
    assert json["last_submission"] == submission_fields
    assert json["uploads_available"] == Settings.submissions_per_student_count_limit - 1


def test_fail_get_submissions_by_verification_code_given_nonexistent_upload_code():
    response = client.get("/submissions/nonexistent_upload_code")
    assert response.status_code == 404


# Verification


def test_pass_get_verifications_download_url(build_models_student, build_models_submission, s3):
    student = build_models_student()
    submission = build_models_submission({"student_id": student.id, "file_name": "file.pdf"})

    mock_generate_download_url_success(s3, {"download_url": "http://s3.com/other_name.pdf"})

    response = client.get(f"/verifications/{submission.verification_code}/download_url")

    assert response.status_code == 200
    json = response.json()
    assert json["download_url"] == "http://s3.com/other_name.pdf"
    assert json["expires_seconds"] == 10 * 60  # 10 min

    # Check that the presigned URL was generated for the file of submission

    assert s3.generate_download_url.call_args[0][0] == submission.file_name


def test_fail_get_verifications_download_url_given_nonexistent_verification_code():
    response = client.get("/verifications/nonexistent_code/download_url")
    assert response.status_code == 404
