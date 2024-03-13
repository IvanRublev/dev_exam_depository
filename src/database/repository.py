from sqlalchemy import create_engine, desc, distinct
from sqlalchemy.orm import Session, sessionmaker

from src.database.models.error import Error
from src.database.models.submission import Submission
from src.database.models.student import Student
from src.settings import Settings

_engine = create_engine(Settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def add_student(session: Session, **attrs: dict):
    """Adds a new student to the database.

    Args:
        session (Session): The database session.
        **attrs (dict): Student attributes.

    Returns:
        Student: The newly created student.
    """
    new_student = Student(**attrs)
    session.add(new_student)
    session.commit()
    return new_student


def student_list_summary(session: Session):
    """Retrieves summary information about all students and their submissions.

    Args:
        session (Session): The database session.

    Returns:
        dict: A dictionary containing the total number of students, total number of submissions, and a list of students.
    """
    with session.begin():
        total_students = session.query(Student).count()
        total_submissions = session.query(distinct(Submission.student_id)).count()
        students = session.query(Student).all()
    return {"totals": {"total_students": total_students, "total_submissions": total_submissions}, "students": students}


def student_by_nickname(session: Session, nickname):
    """Retrieves a student from the database by their nickname.

    Args:
        session (Session): The database session.
        nickname (str): The nickname of the student.

    Returns:
        Student: The student with the specified nickname, or None if not found.
    """
    student = session.query(Student).filter(Student.nickname == nickname).first()
    return student


def student_by_upload_code(session: Session, upload_code: str):
    """Retrieves a student from the database by their upload code.

    Args:
        session (Session): The database session.
        upload_code (str): The upload code of the student.

    Returns:
        Student: The student with the specified upload code, or None if not found.
    """
    student = session.query(Student).filter(Student.upload_code == upload_code).first()
    return student


def is_student_submission_uploads_limit_reached(session: Session, student_id: int):
    """Checks if the student has reached the submission uploads limit.

    Args:
        session (Session): The database session.
        student_id (int): The ID of the student.

    Returns:
        bool: True if the student has reached the submission uploads limit, False otherwise.
    """
    submissions_count = session.query(Submission).filter(Submission.student_id == student_id).count()
    return submissions_count >= Settings.submissions_per_student_count_limit


def student_submission_uploads_available(session: Session, student_id: int):
    """Retrieves the number of submission uploads available to the student.

    Args:
        session (Session): The database session.
        student_id (int): The ID of the student.

    Returns:
        int: The number of submission uploads available.
    """
    submissions_count = session.query(Submission).filter(Submission.student_id == student_id).count()
    return Settings.submissions_per_student_count_limit - submissions_count


def previous_submission_file_name(session: Session, student_id: int):
    """Retrieves the file name on the storage service of the second most recent submission made by the student.

    Args:
        session (Session): The database session.
        student_id (int): The ID of the student.

    Returns:
        str: The file name on the storage service of the second most recent submission, or None if not found.
    """
    recent_submissions = (
        session.query(Submission)
        .filter(Submission.student_id == student_id)
        .order_by(desc(Submission.id))
        .limit(2)
        .all()
    )
    second_submission = recent_submissions[1] if len(recent_submissions) > 1 else None

    if not second_submission:
        return None

    return second_submission.file_name


def add_submission(session: Session, **attrs: dict):
    """Adds a new submission to the database.

    Args:
        session (Session): The database session.
        **attrs (dict): Submission attributes.

    Returns:
        Submission: The newly created submission.
    """
    new_submission = Submission(**attrs)
    session.add(new_submission)
    session.commit()
    return new_submission


def submission_by_verification_code(session: Session, verification_code: str):
    """Retrieves a submission from the database by its verification code.

    Args:
        session (Session): The database session.
        verification_code (str): The verification code of the submission.

    Returns:
        Submission: The submission with the specified verification code, or None if not found.
    """
    submission = session.query(Submission).filter(Submission.verification_code == verification_code).first()
    return submission


def last_errors(session: Session, count: int):
    """Retrieves the last N errors from the database.

    Args:
        session (Session): The database session.
        count (int): The number of errors to retrieve.

    Returns:
        list: A list of Error objects representing the last N errors.
    """
    return session.query(Error).order_by(desc(Error.created_at)).limit(count).all()


def add_error(session: Session, detail: str):
    """Adds a new error to the database.

    Args:
        session (Session): The database session.
        detail (str): The error detail.

    Returns:
        Error: The newly created error.
    """
    new_error = Error(detail=detail)
    session.add(new_error)
    session.commit()
    return new_error
