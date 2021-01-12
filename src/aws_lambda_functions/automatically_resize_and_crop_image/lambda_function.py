import logging
import os
import boto3

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

        print(original_s3_object_key)

    # Return nothing.
    return None
