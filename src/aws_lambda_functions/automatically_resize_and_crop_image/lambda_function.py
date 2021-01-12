import logging
import os
import boto3
from PIL import Image
from io import BytesIO

# Configure the logging tool in the AWS Lambda function.
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Initialize constants with parameters to configure.
S3_ACCESS_KEY_ID = os.environ["S3_ACCESS_KEY_ID"]
S3_SECRET_ACCESS_KEY = os.environ["S3_SECRET_ACCESS_KEY"]
S3_DEFAULT_REGION = os.environ["S3_DEFAULT_REGION"]
FILE_STORAGE_NAME = os.environ["FILE_STORAGE_NAME"]

# Create a low-level service client by name using the default session.
s3_client = boto3.client("s3", aws_access_key_id=S3_ACCESS_KEY_ID, aws_secret_access_key=S3_SECRET_ACCESS_KEY)


def lambda_handler(event, context):
    """
    :param event: The AWS Lambda function uses this parameter to pass in event data to the handler.
    :param context: The AWS Lambda function uses this parameter to provide runtime information to your handler.
    """
    # All size parameters (width/height): 220x156, 88x88, 64x64, 40x40.
    sizes = [
        {"width": 220, "height": 156},
        {"width": 88, "height": 88},
        {"width": 64, "height": 64},
        {"width": 40, "height": 40}
    ]

    # https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
    for key in event.get("Records"):
        # Define the value of the S3 bucket object key.
        try:
            original_s3_object_key = key["s3"]["object"]["key"]
        except Exception as error:
            logger.error(error)
            raise Exception(error)

        # Grab the original source file.
        try:
            original_s3_object = s3_client.Object(bucket_name=FILE_STORAGE_NAME, key=original_s3_object_key)
        except Exception as error:
            logger.error(error)
            raise Exception(error)
        original_s3_object_body = original_s3_object.get()["Body"].read()

        # Create the image object.
        original_image = Image.open(BytesIO(original_s3_object_body))

        # The file format of the source file.
        buffer_format = original_image.format

        # Resize and crop the image file.
        new_image = original_image.resize((sizes[3]["width"], sizes[3]["height"]), Image.ANTIALIAS)
        buffer = BytesIO()
        new_image.save(buffer, buffer_format)
        buffer.seek(0)

        # Define the new S3 object key.
        split_path = os.path.splitext(original_s3_object_key)
        new_s3_object_key = "{0}_{1}{2}".format(split_path[0], "40x40", split_path[1])

        # Upload the new image.
        new_s3_object = s3_client.Object(bucket_name=FILE_STORAGE_NAME, key=new_s3_object_key)
        new_s3_object.put(Body=buffer)

    # Return nothing.
    return None
