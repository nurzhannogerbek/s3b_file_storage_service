import logging
import os
import json
import boto3

# Configure the logging tool in the AWS Lambda function.
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Initialize constants with parameters to configure.
BUCKET_NAME = os.environ["BUCKET_NAME"]


def lambda_handler(event, context):
    """
    :param event: The AWS Lambda function uses this parameter to pass in event data to the handler.
    :param context: The AWS Lambda function uses this parameter to provide runtime information to your handler.
    """
    # Use AWS Lambda proxy integration.
    try:
        query_string_parameters = event["queryStringParameters"]
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Define all necessary parameters to generate the presigned URL.
    try:
        key = query_string_parameters["key"]
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Create a low-level service client by name using the default session.
    s3_client = boto3.client("s3")

    # Generate the presigned URL for the S3 object.
    try:
        presigned_url = s3_client.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=key,
            Fields=None,
            Conditions=None,
            ExpiresIn=3600
        )
    except Exception as error:
        logging.error(error)
        return None

    # Return the status code 200.
    return {
        "statusCode": 200,
        "body": json.dumps(presigned_url)
    }
