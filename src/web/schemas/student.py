from datetime import datetime
import string
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from src.settings import Settings
from src.web.schemas.submission import Submission


class StudentBase(BaseModel):
    nickname: str = Field(..., max_length=Settings.nickname_max_length)
    first_name: str = Field(..., max_length=Settings.first_name_max_length)
    last_name: str = Field(..., max_length=Settings.last_name_max_length)
    email: EmailStr


def _validate_alpha_punctuation(v):
    for p_char in string.punctuation:
        v = v.replace(p_char, "")

    if not v.isalpha():
        raise ValueError("the value name must contain only alpha characters and punctuation")

    return v


class StudentCreate(StudentBase):
    @field_validator("nickname")
    def nickname_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError("nickname must contain only alphanumeric characters")
        return v

    @field_validator("first_name")
    def first_name_must_be_alpha_punctuation(cls, v):
        return _validate_alpha_punctuation(v)

    @field_validator("last_name")
    def last_name_must_be_alpha_punctuation(cls, v):
        return _validate_alpha_punctuation(v)


class Student(StudentBase):
    id: int
    upload_code: str
    has_submission: bool
    last_submission: Optional[Submission] = None
    created_at: datetime
    model_config = {"from_attributes": True}
