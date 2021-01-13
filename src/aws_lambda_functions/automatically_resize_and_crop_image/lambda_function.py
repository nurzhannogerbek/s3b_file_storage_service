import logging
import os
import boto3
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
            original_s3_object_key = unquote_plus(key["s3"]["object"]["key"])
        except KeyError as error:
            logger.error(error)
            raise Exception(error)

        # Grab the original source file.
        original_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=original_s3_object_key)
        original_s3_object_body = original_s3_object.get()["Body"].read()

        # Read the image file.
        original_image = cv2.imdecode(numpy.asarray(bytearray(original_s3_object_body)), cv2.IMREAD_COLOR)

        # Define the size of the original image file.
        original_image_width, original_image_height = original_image.shape[1], original_image.shape[0]

        # Define the extension of the original image file.
        original_image_file_extension = os.path.splitext(original_s3_object_key)[1].lower()

        for parameter in sizes:
            # Create the unique S3 bucket object key for specific size.
            original_s3_object_key_parts = original_s3_object_key.rsplit('/', 1)
            image_size = "{0}x{1}".format(parameter["width"], parameter["height"])
            new_s3_object_key = "{0}/{1}/{2}".format(
                original_s3_object_key_parts[0].replace("users/", "users_cropped_images/"),
                image_size,
                original_s3_object_key_parts[1]
            )

            # Crop the original image file by center.
            if parameter["width"] < original_image_width:
                new_image_width = parameter["width"]
            else:
                new_image_width = original_image_width
            if parameter["height"] < original_image_height:
                new_image_height = parameter["height"]
            else:
                new_image_height = original_image_height
            x, y = int(original_image_width/2), int(original_image_height/2)
            width, height = int(new_image_width/2), int(new_image_height/2)
            new_image = original_image[y-height:y+height, x-width:x+width]

            # Upload the new image file.
            new_s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=new_s3_object_key)
            new_s3_object.put(Body=cv2.imencode(original_image_file_extension, new_image)[1].tobytes())

    # Return nothing.
    return None
