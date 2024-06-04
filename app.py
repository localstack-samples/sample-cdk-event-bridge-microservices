import aws_cdk as cdk
import os
from stacks.events_stack_primary_region import EventsStackPrimaryRegion
from stacks.events_stack_secondary_region import EventsStackSecondaryRegion
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
REGION_PRIMARY = os.getenv("REGION_PRIMARY")
REGION_SECONDARY = os.getenv("REGION_SECONDARY")


app = cdk.App()

EventsStackPrimaryRegion(
    app, "EventsStackPrimaryRegion", env=cdk.Environment(region=REGION_PRIMARY)
)
EventsStackSecondaryRegion(
    app,
    "EventsStackSecondaryRegion",
    env=cdk.Environment(region=REGION_SECONDARY),
)

app.synth()
