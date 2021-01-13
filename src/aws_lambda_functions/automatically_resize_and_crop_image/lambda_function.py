import logging
import os
import boto3
from io import BytesIO
import cv2

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
        except KeyError as error:
            logger.error(error)
            raise Exception(error)

        # Grab the original source file.
        original_s3_object = s3_client.Object(bucket_name=FILE_STORAGE_NAME, key=original_s3_object_key)
        original_s3_object_body = original_s3_object.get()["Body"].read()

        # Read the image file.
        original_image = cv2.imread(BytesIO(original_s3_object_body))

        # Define the original image file's size.
        original_image_width, original_image_height = original_image.shape[1], original_image.shape[0]

        for parameter in sizes:
            # Create the unique S3 bucket object key for specific size.
            original_s3_object_key_parts = original_s3_object_key.rsplit('/', 1)
            new_s3_object_key = "{0}/{1}x{2}/{3}".format(
                original_s3_object_key_parts[0],
                parameter["width"],
                parameter["height"],
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
            mid_x, mid_y = int(original_image_width / 2), int(original_image_height / 2)
            cw2, ch2 = int(new_image_width / 2), int(new_image_height / 2)
            new_image = original_image[mid_y - ch2:mid_y + ch2, mid_x - cw2:mid_x + cw2]
            buffer = BytesIO()
            new_image.save(buffer, format)
            buffer.seek(0)

            # Upload the new image file.
            new_s3_object_body = s3_client.Object(bucket_name=FILE_STORAGE_NAME, key=new_s3_object_key)
            new_s3_object_body.put(Body=buffer)

    # Return nothing.
    return None
