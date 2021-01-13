import logging
import os
import boto3
import json
from urllib.parse import unquote_plus
import cv2
import numpy

# Configure the logging tool in the AWS Lambda function.
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Initialize constants with parameters to configure.
S3_ACCESS_KEY_ID = os.environ["S3_ACCESS_KEY_ID"]
S3_SECRET_ACCESS_KEY = os.environ["S3_SECRET_ACCESS_KEY"]
S3_DEFAULT_REGION = os.environ["S3_DEFAULT_REGION"]
FILE_STORAGE_NAME = os.environ["FILE_STORAGE_NAME"]

# Create the resource service client.
s3_resource = boto3.resource("s3", aws_access_key_id=S3_ACCESS_KEY_ID, aws_secret_access_key=S3_SECRET_ACCESS_KEY)


def lambda_handler(event, context):
    """
    :param event: The AWS Lambda function uses this parameter to pass in event data to the handler.
    :param context: The AWS Lambda function uses this parameter to provide runtime information to your handler.
    """
    # Make sure that all the necessary arguments for the AWS Lambda function are present.
    try:
        original_s3_object_key = unquote_plus(event["queryStringParameters"]["s3_key"])
    except Exception as error:
        logger.error(error)
        raise Exception(error)
    try:
        body = json.loads(event["body"])
    except Exception as error:
        logger.error(error)
        raise Exception(error)
    try:
        sizes = body["sizes"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)
    try:
        coordinates = body["coordinates"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # Grab the original source file.
    original_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=original_s3_object_key)
    original_s3_object_body = original_s3_object.get()["Body"].read()

    # Read the image file.
    original_image = cv2.imdecode(numpy.asarray(bytearray(original_s3_object_body)), cv2.IMREAD_COLOR)

    # Define the extension of the original image file.
    original_image_file_extension = os.path.splitext(original_s3_object_key)[1].lower()

    # Define the empty list of urls.
    urls = []

    for parameter in sizes:
        # Create the unique S3 bucket object key for specific size.
        original_s3_object_key_parts = original_s3_object_key.rsplit('/', 1)
        image_size = "{0}x{1}".format(parameter["width"], parameter["height"])
        new_s3_object_key = "{0}/{1}/{2}".format(
            original_s3_object_key_parts[0].replace("users/", "users_cropped_images/"),
            image_size,
            original_s3_object_key_parts[1]
        )

        # Crop the original image file. Format: image[start_y:end_y, start_x:end_x].
        new_image = original_image[coordinates["y"]:parameter["height"], coordinates["x"]:parameter["width"]]

        # Upload the new image file.
        new_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=new_s3_object_key)
        new_s3_object.put(Body=cv2.imencode(original_image_file_extension, new_image)[1].tobytes())

        # Add the url address of the new image file to the array.
        url = {
            image_size: "https://{0}.s3.{1}.amazonaws.com/{2}".format(
                FILE_STORAGE_NAME,
                S3_DEFAULT_REGION,
                new_s3_object_key
            )
        }
        urls.append(url)

    # Return the status code 200.
    return {
        "statusCode": 200,
        "body": json.dumps({
            "urls": urls
        })
    }
