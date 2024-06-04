import aws_cdk as cdk
import os
from stacks.events_stack_primary_region import EventsStackPrimary
from stacks.events_stack_secondary_region import EventsStackSecondary
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
REGION_PRIMARY = os.getenv("REGION_PRIMARY")
REGION_SECONDARY = os.getenv("REGION_SECONDARY")


app = cdk.App()

EventsStackPrimary(app, "EventsStackPrimaryRegion", env=cdk.Environment(region=REGION_PRIMARY))
EventsStackSecondary(
    app,
    "EventsStackSecondaryRegion",
    env=cdk.Environment(region=REGION_SECONDARY),
)

app.synth()
