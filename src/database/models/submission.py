import string
import secrets

from sqlalchemy import Column, Integer, ForeignKey, String

from .base import Base
from src.settings import Settings

_alphabet = string.ascii_lowercase + string.digits


def _generate_verification_code():
    return "".join(secrets.choice(_alphabet) for _ in range(0, Settings.verification_code_length))


class Submission(Base):
    """Model of a student submission.

    Automatically initialised properties:
        verification_code (str): The verification code for the submission.
    """

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    md5 = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)

    student_id = Column(Integer, ForeignKey("students.id"))

    # generated
    verification_code = Column(String, nullable=False, default=_generate_verification_code)
