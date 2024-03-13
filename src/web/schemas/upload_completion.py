from typing import Optional

from pydantic import BaseModel, Field

from src.web.schemas.submission import SubmissionBase


class UploadCompletion(BaseModel):
    """Schema for completion status of a submission upload.

    Represents the number of uploads remaining and the metadata of the last submission.
    """

    class SubmissionMetadata(SubmissionBase):
        file_name: str = Field(..., exclude=True)

    uploads_available: int
    has_submission: bool
    last_submission: Optional[SubmissionMetadata] = None
