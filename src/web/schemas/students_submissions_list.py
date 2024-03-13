from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StudentsSubmissionsList(BaseModel):
    """Schema for the list of students and their submissions.

    Represents statistics about total number of students and submissions, and a list of students with their submissions.
    """

    class Totals(BaseModel):
        total_students: int
        total_submissions: int

    class StudentSummary(BaseModel):
        class StudentSubmissionSummary(BaseModel):
            created_at: datetime
            verification_code: str

        nickname: str
        first_name: str
        last_name: str
        has_submission: bool
        last_submission: Optional[StudentSubmissionSummary] = None
        model_config = {"from_attributes": True}

    totals: Totals
    students: list[StudentSummary]
    model_config = {"from_attributes": True}
