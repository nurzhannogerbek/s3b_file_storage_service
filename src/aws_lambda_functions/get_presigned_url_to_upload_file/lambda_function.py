import logging
import os
import json
import boto3
from urllib.parse import unquote_plus

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
    # Define all necessary parameters to generate the presigned URL.
    try:
        query_string_parameters = event["queryStringParameters"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)
    try:
        key = unquote_plus(query_string_parameters["key"])
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Generate the presigned URL for the S3 object.
    try:
        presigned_url = s3_client.generate_presigned_post(
            Bucket=FILE_STORAGE_NAME,
            Key=key,
            Fields=None,
            Conditions=None,
            ExpiresIn=60
        )
    except Exception as error:
        logging.error(error)
        return None

    # Return the status code 200.
    return {
        "statusCode": 200,
        "body": json.dumps({
            "data": presigned_url,
            "url": "https://{0}.s3.{1}.amazonaws.com/{2}".format(FILE_STORAGE_NAME, S3_DEFAULT_REGION, key)
        })
    }
