import logging
import os
import boto3
from urllib.parse import unquote_plus
from PIL import Image
from io import BytesIO
import base64

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


def resize_image_file(**kwargs):
    # Check if the input dictionary has all the necessary keys.
    try:
        image_file = kwargs["image_file"]
        image_file_width = kwargs["image_file_width"]
        image_file_height = kwargs["image_file_height"]
        width = kwargs["width"]
        height = kwargs["height"]
        upscale = kwargs["upscale"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # Check the dimensions.
    if image_file_width <= width and image_file_height <= height and not upscale:
        dimension = (image_file_width, image_file_height)
    else:
        if width > 90 and height > 90:
            if image_file_width > image_file_height:
                ratio = width / float(image_file_width)
                dimension = (width, int(image_file_height * ratio))
            else:
                ratio = height / float(image_file_height)
                dimension = (int(image_file_width * ratio), height)
        else:
            if image_file_width < image_file_height:
                ratio = width / float(image_file_width)
                dimension = (width, int(image_file_height * ratio))
            else:
                ratio = height / float(image_file_height)
                dimension = (int(image_file_width * ratio), height)

    # Resize the original image file.
    try:
        resized_image_file = image_file.resize(dimension)
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Return the resized image file.
    return resized_image_file


def lambda_handler(event, context):
    """
    :param event: The AWS Lambda function uses this parameter to pass in event data to the handler.
    :param context: The AWS Lambda function uses this parameter to provide runtime information to your handler.
    """
    # Define all necessary parameters to generate the presigned URL.
    try:
        query_string_parameters = event["queryStringParameters"]
        key = unquote_plus(query_string_parameters["key"])
        width = query_string_parameters["width"]
        height = query_string_parameters["height"]
        quality = query_string_parameters.get("quality", 75)
        upscale = query_string_parameters.get("upscale", False)
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Grab the original source file from the S3 bucket.
    try:
        s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=key)
        s3_object_body = s3_object.get()["Body"].read()
    except Exception as error:
        logger.error(error)
        raise Exception(error)

    # Read the original image file.
    image_file = Image.open(BytesIO(s3_object_body))

    # Define the MIME type of the original image file.
    image_file_mimetype = image_file.get_format_mimetype()

    # Define the format of the original image file.
    image_file_format = image_file.format

    # Define the width and height of the the original image file.
    image_file_width, image_file_height = image_file.size

    # Resize the original image file.
    resized_image_file = resize_image_file(
        image_file=image_file,
        image_file_width=image_file_width,
        image_file_height=image_file_height,
        width=width,
        height=height,
        upscale=upscale
    )

    # Convert PIL Image to Base64 string.
    buffer = BytesIO()
    resized_image_file.save(buffer, format=image_file_format, optimize=True, quality=quality)
    binary_image_file = buffer.getvalue()

    # Return the resized image as Base64 string.
    return {
        "statusCode": 200,
        "body": base64.b64encode(binary_image_file),
        "isBase64Encoded": True,
        "headers": {
            'Content-Type': image_file_mimetype
        }
    }
