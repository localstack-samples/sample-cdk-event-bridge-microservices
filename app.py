import aws_cdk as cdk
import os
from stacks._lambda.consumer import S3_BUCKET_NAME
from stacks.events_stack_primary import EVENT_BUS_NAME_SECONDARY_REGION, EventsStackPrimary
from stacks.events_stack_secondary import EventsStackSecondary
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_ID_SECONDARY = os.getenv("ACCOUNT_ID_SECONDARY")
REGION_PRIMARY = os.getenv("REGION_PRIMARY")
REGION_SECONDARY = os.getenv("REGION_SECONDARY")
EVENT_BUS_NAME_SECONDARY_REGION = os.getenv("EVENT_BUS_NAME_SECONDARY_REGION")
EVENT_BUS_NAME_SECONDARY_ACCOUNT = os.getenv("EVENT_BUS_NAME_SECONDARY_ACCOUNT")
S3_BUCKET_NAME_ONE = os.getenv("S3_BUCKET_NAME_ONE")
S3_BUCKET_NAME_TWO = os.getenv("S3_BUCKET_NAME_TWO")


app = cdk.App()

EventsStackPrimary(
    app, "EventsStackPrimary", env=cdk.Environment(region=REGION_PRIMARY, account=ACCOUNT_ID)
)
EventsStackSecondary(
    app,
    "EventsStackSecondaryRegion",
    env=cdk.Environment(region=REGION_SECONDARY, account=ACCOUNT_ID),
    event_bus_name=EVENT_BUS_NAME_SECONDARY_REGION,
    bucket_name=S3_BUCKET_NAME_ONE,
)
EventsStackSecondary(
    app,
    "EventsStackSecondaryAccount",
    env=cdk.Environment(region=REGION_PRIMARY, account=ACCOUNT_ID_SECONDARY),
    event_bus_name=EVENT_BUS_NAME_SECONDARY_ACCOUNT,
    bucket_name=S3_BUCKET_NAME_TWO,
)

app.synth()
