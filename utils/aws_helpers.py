import boto3
from config import Config
import io
import uuid


def get_sns_client():
    return boto3.client("sns", region_name=Config.AWS_REGION)


def publish_sns_notification(subject, message):
    """
    Publish a message to AWS SNS topic.
    Returns SNS response.
    """
    if not Config.SNS_TOPIC_ARN:
        raise ValueError("SNS_TOPIC_ARN is not configured.")

    sns_client = get_sns_client()

    response = sns_client.publish(
        TopicArn=Config.SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=message
    )
    return response


def get_s3_client():
    return boto3.client("s3", region_name=Config.AWS_REGION)


def upload_text_receipt_to_s3(reservation_data, folder="receipts"):
    """
    Create a simple text receipt in memory and upload it to S3.
    Returns the S3 object key.
    """
    receipt_text = (
        f"Smart Parking Reservation Receipt\n"
        f"---------------------------------\n"
        f"Reservation ID: {reservation_data.get('reservation_id')}\n"
        f"User ID: {reservation_data.get('user_id')}\n"
        f"User Name: {reservation_data.get('user_name')}\n"
        f"User Email: {reservation_data.get('user_email')}\n"
        f"Slot ID: {reservation_data.get('slot_id')}\n"
        f"Slot Number: {reservation_data.get('slot_number')}\n"
        f"Zone: {reservation_data.get('zone')}\n"
        f"Vehicle Number: {reservation_data.get('vehicle_number')}\n"
        f"Reservation Start: {reservation_data.get('reservation_start')}\n"
        f"Reservation End: {reservation_data.get('reservation_end')}\n"
        f"Status: {reservation_data.get('status')}\n"
    )

    file_bytes = io.BytesIO(receipt_text.encode("utf-8"))
    object_key = f"{folder}/reservation_{reservation_data.get('reservation_id')}_{uuid.uuid4().hex}.txt"

    s3_client = get_s3_client()
    s3_client.upload_fileobj(
        Fileobj=file_bytes,
        Bucket=Config.S3_BUCKET_NAME,
        Key=object_key,
        ExtraArgs={"ContentType": "text/plain"}
    )

    return object_key


def generate_presigned_file_url(object_key, expires_in=3600):
    """
    Generate a temporary URL to open a private S3 object.
    """
    if not object_key:
        return None

    s3_client = get_s3_client()
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": Config.S3_BUCKET_NAME,
            "Key": object_key
        },
        ExpiresIn=expires_in
    )