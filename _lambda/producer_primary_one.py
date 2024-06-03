import boto3
import logging
from datetime import datetime, timezone
import json

REGION_MAIN = "us-east-1"
EVENT_BUS_NAME_PRIMARY = "event_bus_primary"
SOURCE_PRODUCER_PRIMARY_ONE = "producer-primary-one"

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create EventBridge client
events_client = boto3.client("events")


def lambda_handler(event, context):
    entries = [
        {
            "EventBusName": EVENT_BUS_NAME_PRIMARY,
            "Source": SOURCE_PRODUCER_PRIMARY_ONE,
            "DetailType": "update-account-command",
            "Detail": json.dumps(event),
            "Time": datetime.now(timezone.utc),
        }
    ]

    try:
        result = events_client.put_events(Entries=entries)
        logger.info("Event sent successfully: %s", result)
        return result
    except Exception as error:
        logger.error("Error sending event: %s", error)
        raise error
