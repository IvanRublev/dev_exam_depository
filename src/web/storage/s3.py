import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
import os
import uuid

from src.logger import logger
from src.settings import Settings


class S3:
    """A class to operate files on an AWS S3 like storage.

    This class provides methods to upload, remove, and generate download URLs for files on S3.
    """

    def __init__(self, endpoint_url):
        self._s3_client = boto3.client(
            "s3", endpoint_url=endpoint_url, config=Config(signature_version=Settings.aws_s3_signature_version)
        )

    def upload_file(self, file_object):
        """Uploads a file to the S3 bucket and returns the file attributes.

        Args:
            file_object: The [file-like object](https://docs.python.org/3/glossary.html#term-file-like-object)
                         to be uploaded.

        Returns:
            dict: A dictionary containing the file size_bytes, md5, and file_name.
        """
        file_extension = os.path.splitext(file_object.filename)[1]
        file_name = f"{uuid.uuid4()}{file_extension}"

        # Set the threshold for multipart upload to be larger than the max submission size
        # to force one part upload, so we have md5 and size_bytes of the whole file in response
        # from S3 instead of similar values for multiple parts.
        config = TransferConfig(multipart_threshold=Settings.submission_max_size_bytes * 10)

        self._s3_client.upload_fileobj(
            Fileobj=file_object.file, Bucket=Settings.aws_s3_bucket_name, Key=file_name, Config=config
        )

        response = self._s3_client.head_object(Bucket=Settings.aws_s3_bucket_name, Key=file_name)

        logger.info(f'File "{file_object.filename}" has been persisted on S3 as "{file_name}".')

        size_bytes = response["ContentLength"]
        md5 = response["ETag"]

        return {"size_bytes": size_bytes, "md5": md5, "file_name": file_name}

    def remove_file(self, file_name):
        """Removes a file from the S3 bucket.

        Args:
            file_name (str): The name of the file to be removed.

        Returns:
            dict: A dictionary containing the response from the S3 service.
        """
        return self._s3_client.delete_object(Bucket=Settings.aws_s3_bucket_name, Key=file_name)

    def generate_download_url(self, file_name):
        """Generates a pre-signed URL for downloading a file from the S3 bucket.

        Args:
            file_name: The name of the file to generate the download URL for.

        Returns:
            dict: A dictionary containing the download URL and the expiration time in seconds.
        """
        url = self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": Settings.aws_s3_bucket_name, "Key": file_name},
            ExpiresIn=Settings.download_url_expires_seconds,
        )
        return {"download_url": url, "expires_seconds": Settings.download_url_expires_seconds}


def _init_s3_shared_instance():
    if os.environ["ENV"] in ["PROD", "STAGE"]:
        return S3(endpoint_url=Settings.aws_s3_endpoint_url)
    else:
        return None


s3_shared_instance = _init_s3_shared_instance()
