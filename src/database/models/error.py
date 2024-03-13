from sqlalchemy import Column, Integer, String

from .base import Base


class Error(Base):
    """Model to store errors that occur when uploading to S3."""

    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    detail = Column(String, nullable=False)
