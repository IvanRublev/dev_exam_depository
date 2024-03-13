import os
import toml

with open("pyproject.toml", "r") as file:
    _pyproject_content = toml.load(file)


class Settings:
    """Represents the settings for the application.

    Some of them are loaded from environment variables, have hardcoded values, or loaded from the pyproject.toml .
    """

    # Loaded from environment variables

    auth_token: str = os.environ["AUTH_TOKEN"]
    aws_s3_bucket_name: str = os.environ["AWS_S3_BUCKET_NAME"]
    aws_s3_endpoint_url: str = os.environ["AWS_S3_ENDPOINT_URL"]
    database_url: str = os.environ["DATABASE_URL"]
    port: int = int(os.getenv("PORT", 8000))

    # Hardcoded

    aws_s3_signature_version: str = "s3v4"
    download_url_expires_seconds: int = 10 * 60  # 10 min
    first_name_max_length: int = 254
    last_name_max_length: int = 254
    nickname_max_length: int = 12
    submission_expire_seconds: int = 3 * 24 * 60 * 60  # 3 days
    submission_max_size_bytes: int = 3 * 1024 * 1024  # 3 MB
    submissions_per_student_count_limit: int = 5
    upload_code_length: int = 8
    verification_code_length: int = 9

    # From pyproject.toml

    app_name = _pyproject_content["tool"]["poetry"]["name"]
    app_description = _pyproject_content["tool"]["poetry"]["description"]
    app_version = _pyproject_content["tool"]["poetry"]["version"]
