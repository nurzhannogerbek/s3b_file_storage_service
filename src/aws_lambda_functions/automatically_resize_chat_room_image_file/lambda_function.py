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


def resize_image_file(**kwargs):
    # Check if the input dictionary has all the necessary keys.
    try:
        image_file = kwargs["image_file"]
        image_file_width = kwargs["image_file_width"]
        image_file_height = kwargs["image_file_height"]
        new_image_file_width = kwargs["new_image_file_width"]
        new_image_file_height = kwargs["new_image_file_height"]
        interpolation = kwargs["interpolation"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # The code below resizes an image making it square and keeping aspect ration at the same time.
    # Also the code is suitable for 3 channels (colored) images as well.
    channel = None if len(image_file.shape) < 3 else image_file.shape[2]
    dimension = (new_image_file_width, new_image_file_height)
    if image_file_height == image_file_width:
        return cv2.resize(image_file, dimension, interpolation)
    if image_file_height > image_file_width:
        difference = image_file_height
    else:
        difference = image_file_width
    x_position = int((difference - image_file_width) / 2.)
    y_position = int((difference - image_file_height) / 2.)
    if channel is None:
        mask = numpy.zeros((difference, difference), dtype=image_file.dtype)
        mask[y_position:y_position+image_file_height, x_position:x_position+image_file_width] = \
            image_file[:image_file_height, :image_file_width]
    else:
        mask = numpy.zeros((difference, difference, channel), dtype=image_file.dtype)
        mask[y_position:y_position+image_file_height, x_position:x_position+image_file_width, :] = \
            image_file[:image_file_height, :image_file_width, :]
    return cv2.resize(mask, dimension, interpolation=interpolation)


def put_s3_object_in_bucket(**kwargs):
    # Check if the input dictionary has all the necessary keys.
    try:
        s3_object_key = kwargs["s3_object_key"]
        image_file_extension = kwargs["image_file_extension"]
        image_file = kwargs["image_file"]
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # Put the object in the Amazon S3 Bucket.
    try:
        s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=s3_object_key)
        s3_object.put(Body=cv2.imencode(image_file_extension, image_file)[1].tobytes())
    except KeyError as error:
        logger.error(error)
        raise Exception(error)

    # Return nothing.
    return None


def lambda_handler(event, context):
    """
    :param event: The AWS Lambda function uses this parameter to pass in event data to the handler.
    :param context: The AWS Lambda function uses this parameter to provide runtime information to your handler.
    """
    # https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
    for key in event.get("Records"):
        # Define the value of the S3 bucket object's key.
        try:
            s3_object_key = unquote_plus(key["s3"]["object"]["key"])
        except KeyError as error:
            logger.error(error)
            raise Exception(error)

        # Grab the original source file from the S3 bucket.
        try:
            s3_object = s3_resource.Object(bucket_name=FILE_STORAGE_NAME, key=s3_object_key)
            s3_object_body = s3_object.get()["Body"].read()
        except Exception as error:
            logger.error(error)
            raise Exception(error)

        # Read the image file.
        image_file = numpy.asarray(bytearray(s3_object_body), dtype="uint8")
        image_file = cv2.imdecode(image_file, cv2.IMREAD_COLOR)

        # Define the width and height of the the original image file.
        image_file_height, image_file_width = image_file.shape[:2]

        # Split the original s3 object key value to the several parts.
        s3_object_key_parts = s3_object_key.rsplit('/', 1)

        # Define several variables that will be used in the future.
        s3_object_key_part = s3_object_key_parts[0].replace("chat_rooms/", "chat_rooms_images/")
        image_file_name = s3_object_key_parts[-1]
        image_file_extension = os.path.splitext(image_file_name)[1].lower()

        # thumb: "800x800".
        thumb_image_file = resize_image_file(
            image_file=image_file,
            image_file_width=image_file_width,
            image_file_height=image_file_height,
            new_image_file_width=800,
            new_image_file_height=800,
            interpolation=cv2.INTER_LINEAR
        )
        put_s3_object_in_bucket(
            s3_object_key="{0}/{1}/{2}".format(s3_object_key_part, "thumb", image_file_name),
            image_file_extension=image_file_extension,
            image_file=thumb_image_file
        )

        # thumb_x2: "1280x1280".
        thumb_x2_image_file = resize_image_file(
            image_file=image_file,
            image_file_width=image_file_width,
            image_file_height=image_file_height,
            new_image_file_width=1280,
            new_image_file_height=1280,
            interpolation=cv2.INTER_LINEAR
        )
        put_s3_object_in_bucket(
            s3_object_key="{0}/{1}/{2}".format(s3_object_key_part, "thumb_x2", image_file_name),
            image_file_extension=image_file_extension,
            image_file=thumb_x2_image_file
        )

        # modal: "2560x2560".
        modal_image_file = resize_image_file(
            image_file=image_file,
            image_file_width=image_file_width,
            image_file_height=image_file_height,
            new_image_file_width=2560,
            new_image_file_height=2560,
            interpolation=cv2.INTER_LINEAR
        )
        put_s3_object_in_bucket(
            s3_object_key="{0}/{1}/{2}".format(s3_object_key_part, "modal", image_file_name),
            image_file_extension=image_file_extension,
            image_file=modal_image_file
        )

        # preload: "10x10".
        preload_image_file = resize_image_file(
            image_file=image_file,
            image_file_width=image_file_width,
            image_file_height=image_file_height,
            new_image_file_width=10,
            new_image_file_height=10,
            interpolation=cv2.INTER_LINEAR
        )
        put_s3_object_in_bucket(
            s3_object_key="{0}/{1}/{2}".format(s3_object_key_part, "preload", image_file_name),
            image_file_extension=image_file_extension,
            image_file=preload_image_file
        )

        # quoted: "90x90".
        quoted_image_file = resize_image_file(
            image_file=image_file,
            image_file_width=image_file_width,
            image_file_height=image_file_height,
            new_image_file_width=90,
            new_image_file_height=90,
            interpolation=cv2.INTER_LINEAR
        )
        put_s3_object_in_bucket(
            s3_object_key="{0}/{1}/{2}".format(s3_object_key_part, "quoted", image_file_name),
            image_file_extension=image_file_extension,
            image_file=quoted_image_file
        )

    # Return nothing.
    return None
