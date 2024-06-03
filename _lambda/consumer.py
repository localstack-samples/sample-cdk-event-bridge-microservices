import json
import boto3
import logging
from datetime import datetime, timezone

S3_BUCKET_NAME = "eventbridge-secondary-s3-bucket"

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    # Generate a unique file name based on the current timestamp
    file_name = f"event_{datetime.now(timezone.utc)}.json"

    # Save the event to the S3 bucket
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(event),
            ContentType="application/json",
        )
        logger.info("Event successfully saved to S3 bucket: %s", S3_BUCKET_NAME)
    except Exception as e:
        logger.error("Error saving event to S3: %s", str(e))
        raise e

    return {"statusCode": 200, "body": json.dumps("Event processed and saved to S3 successfully.")}
