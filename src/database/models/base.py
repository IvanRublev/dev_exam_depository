from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

DeclarativeBase = declarative_base()


class Base(DeclarativeBase):
    """Base class for all database models.

    It defines two properties (columns) common to all models: `created_at` and `updated_at`.

    Automatically initialised properties:
        created_at (DateTime): The timestamp of when the model instance was created.
        updated_at (DateTime): The timestamp of when the model instance was last updated.
    """

    __abstract__ = True

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
