import secrets
import string

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base
from src.settings import Settings

_alphabet = string.ascii_uppercase + string.digits


def _generate_upload_code():
    return "".join(secrets.choice(_alphabet) for _ in range(0, Settings.upload_code_length))


class Student(Base):
    """Model of a student.

    Automatically initialised properties:
        id (int): The unique identifier of the student.
        upload_code (str): The upload code generated for the student.

    Read-only properies:
        submissions (list): A list of submissions made by the student.
        has_submission (bool): Indicates whether the student has made any submissions.
        last_submission (Submission): The last submission made by the student, or None if no submissions exist.
    """

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    upload_code = Column(String, nullable=False, default=_generate_upload_code)

    submissions = relationship("Submission", backref="student", viewonly=True)

    @property
    def has_submission(self):
        return len(self.submissions) > 0

    @property
    def last_submission(self):
        if self.submissions:
            return sorted(self.submissions, key=lambda submission: submission.id, reverse=True)[0]
        else:
            return None
