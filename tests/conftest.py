import json
import pytest

from faker import Faker
from pydantic import ValidationError
from unittest.mock import Mock

from src.database.models.base import Base
from src.database import repository
from src.settings import Settings
from src.web import schemas
from src.web.api import app, get_db, get_s3
from src.web.storage.s3 import S3

fake = Faker()


# fixtures for HTTP requests


@pytest.fixture
def auth_header():
    def _auth_header(token: str = Settings.auth_token):
        return {"Authorization": f"Bearer {token}"}

    return _auth_header


# fixtures for database


@pytest.fixture(scope="function", autouse=True)
def db_session():
    session = repository.SessionLocal()

    # inject test session into the app,
    # so we use the same session in test and unit under test
    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.rollback()  # for case if we have an uncommitted transaction due to an exception

    # Drop all records in all tables after each test
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())

    session.commit()
    session.close()


@pytest.fixture(scope="function")
def build_models_student(db_session, build_json_student):
    def _build_models_student(attrs={}):
        upd_attrs = {**build_json_student(), **attrs}
        student = repository.add_student(session=db_session, **upd_attrs)

        return student

    return _build_models_student


@pytest.fixture(scope="function")
def build_models_submission(db_session):
    def _build_models_submission(attrs={}):
        """
        Pass existing student id value as part of attrs dictionatry
        """
        upd_attrs = {"student_id": 1, "file_name": fake.uri(), "md5": fake.md5(), "size_bytes": 1000, **attrs}
        student = repository.add_submission(session=db_session, **upd_attrs)

        return student

    return _build_models_submission


# fixtures for schemas


@pytest.fixture(scope="function")
def build_json_student():
    def _build_json_student(attrs={}):
        upd_attrs = {
            "nickname": fake.user_name()[:12],
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            **attrs,
        }
        return upd_attrs

    return _build_json_student


# fixtures for s3 storage


@pytest.fixture(scope="function", autouse=True)
def s3():
    s3_mock = Mock(spec=S3)
    mock_upload_file_success_json(s3_mock)
    mock_remove_file_success(s3_mock)
    mock_generate_download_url_success(s3_mock)

    app.dependency_overrides[get_s3] = lambda: s3_mock

    return s3_mock


# mocks for s3 storage


def mock_upload_file_success_json(s3_mock, attrs={}):
    md5 = f'"{fake.md5()}"'  # md5 is wrapped in quotes in the response from S3
    upd_attrs = {"size_bytes": 1000, "md5": md5, "file_name": f"{fake.word()}.pdf", **attrs}

    s3_mock.upload_file.return_value = upd_attrs

    return s3_mock


def mock_upload_file_failure(s3_mock, side_effect):
    s3_mock.upload_file.side_effect = side_effect
    return s3_mock


def mock_remove_file_success(s3_mock, attrs={}):
    upd_attrs = {"ResponseMetadata": {"HTTPStatusCode": 204}, **attrs}
    s3_mock.remove_file.return_value = upd_attrs
    return s3_mock


def mock_generate_download_url_success(s3_mock, attrs={}):
    upd_attrs = {"download_url": fake.uri(), "expires_seconds": Settings.download_url_expires_seconds, **attrs}
    s3_mock.generate_download_url.return_value = upd_attrs
    return s3_mock


# assertions


def assert_validation_error(schemas_constructor_fun, failed_field, message_part):
    """
    Asserts that construction of a schemas class raises an ValidationError exception
    """
    try:
        schemas_constructor_fun()
        raise AssertionError()
    except ValidationError as e:
        errors = e.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (failed_field,)
        assert message_part in errors[0]["msg"]


# dump functions


def dump_schemas_student(instance):
    return dump_schema_fun(schemas.student.Student, instance)


def dump_schemas_submission(instance):
    return dump_schema_fun(schemas.submission.Submission, instance)


def dump_schema_fun(cls, instance):
    schema_instance = cls.model_validate(instance)
    return json.loads(schema_instance.model_dump_json())
