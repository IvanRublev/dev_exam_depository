from datetime import datetime
from pydantic import BaseModel


class SubmissionBase(BaseModel):
    file_name: str
    md5: str
    size_bytes: int
    verification_code: str
    created_at: datetime


class Submission(SubmissionBase):
    """Schema for a student's submission."""

    model_config = {"from_attributes": True}
