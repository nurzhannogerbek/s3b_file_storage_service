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
        image_file_sizes = body["sizes"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)
    try:
        coordinates = body["coordinates"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)
    try:
        scale = body["scale"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # Check which folder the client is going to work with.
    if original_s3_object_key.startswith("chat_rooms/"):
        return {
            "statusCode": 403,
            "body": json.dumps({
                "errorMessage": "You can't change the size of images in the 'chat_rooms' folder."
            })
        }

    # Grab the original source file from the S3 bucket.
    try:
        original_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=original_s3_object_key)
        original_s3_object_body = original_s3_object.get()["Body"].read()
    except Exception as error:
        logger.error(error)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "errorMessage": error
            })
        }

    # Read the image file.
    original_image_file = cv2.imdecode(numpy.asarray(bytearray(original_s3_object_body)), cv2.IMREAD_COLOR)

    # Define the extension of the original image file.
    original_image_file_extension = os.path.splitext(original_s3_object_key)[1].lower()

    # Define the empty list of urls.
    urls = []

    for parameter in image_file_sizes:
        # Create the unique S3 bucket object key for the new image file.
        original_s3_object_key_parts = original_s3_object_key.split('/')
        original_s3_object_key_parts[0] = "{0}{1}".format(original_s3_object_key_parts[0], "_images")
        temporary_s3_object_key = "/".join(original_s3_object_key_parts)
        original_s3_object_key_parts = temporary_s3_object_key.rsplit('/', 1)
        image_file_size = "{0}x{1}".format(parameter["width"], parameter["height"])
        new_s3_object_key = "{0}/{1}/{2}".format(
            original_s3_object_key_parts[0],
            image_file_size,
            original_s3_object_key_parts[1]
        )

        # Crop the original image file and then resize it.
        try:
            x = coordinates["x"]
            y = coordinates["y"]
            width = coordinates["width"]
            height = coordinates["height"]
            cropped_image_file = original_image_file[y:height, x:width]
            resized_image_file = cv2.resize(
                cropped_image_file,
                (int(parameter["width"]*scale), int(parameter["height"]*scale))
            )
        except Exception as error:
            logger.error(error)
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "errorMessage": "The image file may be damaged."
                })
            }

        # Upload the new image file to the S3 bucket.
        new_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=new_s3_object_key)
        new_s3_object.put(Body=cv2.imencode(original_image_file_extension, resized_image_file)[1].tobytes())

        # Add the url address of the new image file to the array.
        url = {
            image_file_size: "https://{0}.s3.{1}.amazonaws.com/{2}".format(
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
