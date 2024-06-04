from aws_cdk import (
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sqs as sqs,
)
import aws_cdk as cdk
import aws_cdk.aws_iam as iam
from constructs import Construct
import os

from dotenv import load_dotenv

load_dotenv()

REGION_SECONDARY = os.getenv("REGION_SECONDARY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
EVENT_BUS_NAME_SECONDARY = os.getenv("EVENT_BUS_NAME_SECONDARY")
EVENT_BUS_NAME_PRIMARY = os.getenv("EVENT_BUS_NAME_PRIMARY")
SOURCE_PRODUCER_PRIMARY_ONE = os.getenv("SOURCE_PRODUCER_PRIMARY_ONE")
SOURCE_PRODUCER_PRIMARY_TWO = os.getenv("SOURCE_PRODUCER_PRIMARY_TWO")


class EventsStackPrimaryRegion(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Producer 1 lambda microservice
        lambda_producer_one = _lambda.Function(
            self,
            id="ProducerPrimaryOne",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="producer_primary_one.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("./stacks/_lambda/")),
        )

        # Producer 2 lambda microservice
        lambda_producer_two = _lambda.Function(
            self,
            id="ProducerPrimaryTwo",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="producer_primary_two.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("./stacks/_lambda/")),
        )

        lambda_rule = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["events:PutEvents"],
            resources=[
                "arn:aws:events:*:*:event-bus/*"
            ],  # [event_bus_primary.event_bus_arn],
        )
        lambda_producer_one.add_to_role_policy(lambda_rule)
        lambda_producer_two.add_to_role_policy(lambda_rule)

        # Define the event bus in the secondary region
        event_bus_secondary = events.EventBus.from_event_bus_arn(
            self,
            id="EventBusSecondary",
            event_bus_arn=f"arn:aws:events:{REGION_SECONDARY}:{ACCOUNT_ID}:event-bus/{EVENT_BUS_NAME_SECONDARY}",
        )

        # Role to put events from event bus 1 to event bus 2 in region secondary
        role_event_bus_primary_to_secondary = iam.Role(
            self,
            id="EventBusPrimaryToSecondaryRole",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            inline_policies={
                "PutEventsPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["events:PutEvents"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                "arn:aws:events:*:*:event-bus/*"
                            ],  # [event_bus_secondary.event_bus_arn],
                        )
                    ]
                )
            },
        )

        # Event bus 1 central bus in region main region
        event_bus_primary = events.EventBus(
            self, id="EventBusPrimary", event_bus_name=EVENT_BUS_NAME_PRIMARY
        )

        # Rule to send events from producer 1 event bus 1 to event bus 2
        rule_event_bus_secondary = events.Rule(
            self,
            id="RuleEventBusSecondary",
            event_bus=event_bus_primary,
            event_pattern={"source": [SOURCE_PRODUCER_PRIMARY_ONE]},
        )
        rule_event_bus_secondary.add_target(
            targets.EventBus(
                event_bus_secondary, role=role_event_bus_primary_to_secondary
            )
        )

        # Sqs queue as target for all events
        sqs_queue = sqs.Queue(self, "PrimaryQueue")
        sqs_queue.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["sqs:SendMessage"],
                effect=iam.Effect.ALLOW,
                resources=[sqs_queue.queue_arn],
                principals=[iam.ServicePrincipal("events.amazonaws.com")],
            )
        )

        # Rule to send all events from event bus 1 to sqs queue
        rule_sqs_queue = events.Rule(
            self,
            id="RuleSqs",
            event_bus=event_bus_primary,
            event_pattern={
                "source": [SOURCE_PRODUCER_PRIMARY_ONE, SOURCE_PRODUCER_PRIMARY_TWO]
            },
            targets=[targets.SqsQueue(sqs_queue)],
        )

        # TODO add schema
