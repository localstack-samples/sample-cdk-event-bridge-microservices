from aws_cdk import (
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sqs as sqs,
)
import aws_cdk as cdk

import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
from constructs import Construct
import os

from dotenv import load_dotenv

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
EVENT_BUS_NAME_SECONDARY_REGION = os.getenv("EVENT_BUS_NAME_SECONDARY_REGION")
SOURCE_PRODUCER_PRIMARY_ONE = os.getenv("SOURCE_PRODUCER_PRIMARY_ONE")
SOURCE_PRODUCER_PRIMARY_TWO = os.getenv("SOURCE_PRODUCER_PRIMARY_TWO")
SOURCE_PRODUCER_SECONDARY = os.getenv("SOURCE_PRODUCER_SECONDARY")


class EventsStackSecondary(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Consumer lambda microservice
        lambda_consumer = _lambda.Function(
            self,
            id="Consumer",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="consumer.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("./stacks/_lambda/")),
        )

        # Lambda consumer S3 bucket
        bucket_consumer = s3.Bucket(
            self,
            id="S3BucketConsumer",
            bucket_name=S3_BUCKET_NAME,
        )
        role_lambda_consumer_to_s3_bucket = iam.Role(
            self,
            id="LambdaConsumerS3BucketRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        bucket_consumer.grant_write(role_lambda_consumer_to_s3_bucket)

        # Test producer lambda microservice
        lambda_producer = _lambda.Function(
            self,
            id="ProducerSecondary",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="producer_secondary.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("./stacks/_lambda/")),
        )
        lambda_rule = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["events:PutEvents"],
            resources=["arn:aws:events:*:*:event-bus/*"],  # [event_bus_primary.event_bus_arn],
        )
        lambda_producer.add_to_role_policy(lambda_rule)

        # Event bus 2 subscriber bus in region secondary
        event_bus_secondary_region = events.EventBus(
            self, id="EventBusSecondary", event_bus_name=EVENT_BUS_NAME_SECONDARY_REGION
        )

        # Event bridge rule to send events to the consumer lambda
        rule_lambda_consumer = events.Rule(
            self,
            "RuleLambdaConsumer",
            event_bus=event_bus_secondary_region,
            event_pattern={
                "source": [SOURCE_PRODUCER_PRIMARY_ONE],
            },
            targets=[targets.LambdaFunction(lambda_consumer)],
        )

        # Sqs queue as target for all events
        sqs_queue = sqs.Queue(self, "SecondaryQueue")
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
            event_bus=event_bus_secondary_region,
            event_pattern={
                "source": [
                    SOURCE_PRODUCER_PRIMARY_ONE,
                    SOURCE_PRODUCER_PRIMARY_TWO,
                    SOURCE_PRODUCER_SECONDARY,
                ]
            },
            targets=[targets.SqsQueue(sqs_queue)],
        )

        # TODO add schema
