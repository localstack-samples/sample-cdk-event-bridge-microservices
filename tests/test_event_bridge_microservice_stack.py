import queue
import boto3
import json
import os
import time
from typing import Callable, TypeVar

from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_ID_SECONDARY = os.getenv("ACCOUNT_ID_SECONDARY")
ACCOUNT_PROFILE_NAME_SECONDARY = os.getenv("ACCOUNT_PROFILE_NAME_SECONDARY")

ACCESS_KEY_SECONDARY = os.getenv("ACCESS_KEY_SECONDARY")
SECRET_KEY_SECONDARY = os.getenv("SECRET_KEY_SECONDARY")

REGION_PRIMARY = os.getenv("REGION_PRIMARY")
REGION_SECONDARY = os.getenv("REGION_SECONDARY")

STACK_NAME_PRIMARY = os.getenv("STACK_NAME_PRIMARY")
STACK_NAME_SECONDARY_REGION = os.getenv("STACK_NAME_SECONDARY_REGION")
STACK_NAME_SECONDARY_ACCOUNT = os.getenv("STACK_NAME_SECONDARY_ACCOUNT")

SOURCE_PRODUCER_PRIMARY_ONE = os.getenv("SOURCE_PRODUCER_PRIMARY_ONE")
SOURCE_PRODUCER_PRIMARY_TWO = os.getenv("SOURCE_PRODUCER_PRIMARY_TWO")
SOURCE_PRODUCER_SECONDARY = os.getenv("SOURCE_PRODUCER_SECONDARY")


DEFAULT_MESSAGE = {
    "command": "update-account",
    "payload": {"acc_id": "0a787ecb-4015", "sf_id": "baz"},
}

T = TypeVar("T")


def retry(function: Callable[..., T], retries=3, sleep=1.0, sleep_before=0, **kwargs) -> T:
    raise_error = None
    if sleep_before > 0:
        time.sleep(sleep_before)
    retries = int(retries)
    for i in range(0, retries + 1):
        try:
            return function(**kwargs)
        except Exception as error:
            raise_error = error
            time.sleep(sleep)
    raise raise_error


def sqs_collect_messages(
    sqs_client,
    queue_url: str,
    min_events: int,
    wait_time: int = 1,
    retries: int = 3,
) -> list[dict]:
    events = []

    def collect_events() -> None:
        _response = sqs_client.receive_message(QueueUrl=queue_url, WaitTimeSeconds=wait_time)
        messages = _response.get("Messages", [])

        for m in messages:
            events.append(m)
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])

        assert len(events) >= min_events

    retry(collect_events, retries=retries, sleep=0.01)

    return events


def test_cross_region():
    # Create boto3 clients for both regions
    lambda_client_primary_region = boto3.client("lambda", region_name=REGION_PRIMARY)
    lambda_client_secondary_region = boto3.client("lambda", region_name=REGION_SECONDARY)
    cloudformation_client_primary_region = boto3.client(
        "cloudformation", region_name=REGION_PRIMARY
    )
    cloudformation_client_secondary_region = boto3.client(
        "cloudformation", region_name=REGION_SECONDARY
    )
    sqs_client_primary_region = boto3.client("sqs", region_name=REGION_PRIMARY)
    sqs_client_secondary_region = boto3.client("sqs", region_name=REGION_SECONDARY)

    # Get stack resources
    response_cloudformation_primary_region = (
        cloudformation_client_primary_region.describe_stack_resources(StackName=STACK_NAME_PRIMARY)
    )
    response_cloudformation_secondary_region = (
        cloudformation_client_secondary_region.describe_stack_resources(
            StackName=STACK_NAME_SECONDARY_REGION
        )
    )
    lambda_function_names = {
        "ProducerPrimaryOne": None,
        "ProducerPrimaryTwo": None,
        "ProducerSecondary": None,
    }
    queue_urls = {
        "PrimaryQueue": None,
        "SecondaryQueue": None,
    }
    for stack_resources in [
        response_cloudformation_primary_region,
        response_cloudformation_secondary_region,
    ]:
        for resource in stack_resources["StackResources"]:
            if resource["ResourceType"] == "AWS::Lambda::Function":
                lambda_function_name = resource["PhysicalResourceId"]
                for key in lambda_function_names:
                    if key in lambda_function_name:
                        lambda_function_names[key] = lambda_function_name
            if resource["ResourceType"] == "AWS::SQS::Queue":
                queue_url = resource["PhysicalResourceId"]
                for key in queue_urls:
                    if key in queue_url:
                        queue_urls[key] = queue_url

    # Cleanup sqs queues
    sqs_client_primary_region.purge_queue(QueueUrl=queue_urls["PrimaryQueue"])
    sqs_client_secondary_region.purge_queue(QueueUrl=queue_urls["SecondaryQueue"])

    # Invoke lambda producer primary one
    invoke_result_producer_primary_one = lambda_client_primary_region.invoke(
        FunctionName=lambda_function_names["ProducerPrimaryOne"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_primary_one["StatusCode"] == 200

    # Invoke lambda producer secondary one
    invoke_result_producer_primary_one = lambda_client_primary_region.invoke(
        FunctionName=lambda_function_names["ProducerPrimaryTwo"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_primary_one["StatusCode"] == 200

    # Check sqs queue primary for both messages
    messages_primary = sqs_collect_messages(
        sqs_client=sqs_client_primary_region,
        queue_url=queue_urls["PrimaryQueue"],
        min_events=2,
    )
    for message in messages_primary:
        body = json.loads(message["Body"])
        assert (
            body["source"] == SOURCE_PRODUCER_PRIMARY_ONE
            or body["source"] == SOURCE_PRODUCER_PRIMARY_TWO
        )
        assert body["detail"] == DEFAULT_MESSAGE

    # Invoke lambda producer secondary
    invoke_result_producer_secondary = lambda_client_secondary_region.invoke(
        FunctionName=lambda_function_names["ProducerSecondary"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_secondary["StatusCode"] == 200

    # Check sqs queue secondary for fist and third message
    messages_secondary = sqs_collect_messages(
        sqs_client=sqs_client_secondary_region,
        queue_url=queue_urls["SecondaryQueue"],
        min_events=2,  # one from primary region producer one and one from secondary region producer
    )
    for message in messages_secondary:
        body = json.loads(message["Body"])
        assert (
            body["source"] == SOURCE_PRODUCER_PRIMARY_ONE
            or body["source"] == SOURCE_PRODUCER_SECONDARY
        )
        assert body["detail"] == DEFAULT_MESSAGE


def test_cross_account():
    # Create boto3 clients for both accounts
    session_secondary_account = boto3.Session(
        profile_name=ACCOUNT_PROFILE_NAME_SECONDARY,
        region_name=REGION_PRIMARY,
    )

    lambda_client_primary = boto3.client("lambda", region_name=REGION_PRIMARY)
    lambda_client_secondary_account = session_secondary_account.client(
        "lambda",
    )
    cloudformation_client_primary = boto3.client("cloudformation", region_name=REGION_PRIMARY)
    cloudformation_client_secondary_account = session_secondary_account.client(
        "cloudformation",
    )
    sqs_client_primary = boto3.client("sqs", region_name=REGION_PRIMARY)
    sqs_client_secondary_account = session_secondary_account.client(
        "sqs",
    )

    # Get stack resources
    response_cloudformation_primary = cloudformation_client_primary.describe_stack_resources(
        StackName=STACK_NAME_PRIMARY
    )
    response_cloudformation_secondary = (
        cloudformation_client_secondary_account.describe_stack_resources(
            StackName=STACK_NAME_SECONDARY_ACCOUNT
        )
    )
    lambda_function_names = {
        "ProducerPrimaryOne": None,
        "ProducerPrimaryTwo": None,
        "ProducerSecondary": None,
    }
    queue_urls = {
        "PrimaryQueue": None,
        "SecondaryQueue": None,
    }
    for stack_resources in [
        response_cloudformation_primary,
        response_cloudformation_secondary,
    ]:
        for resource in stack_resources["StackResources"]:
            if resource["ResourceType"] == "AWS::Lambda::Function":
                lambda_function_name = resource["PhysicalResourceId"]
                for key in lambda_function_names:
                    if key in lambda_function_name:
                        lambda_function_names[key] = lambda_function_name
            if resource["ResourceType"] == "AWS::SQS::Queue":
                queue_url = resource["PhysicalResourceId"]
                for key in queue_urls:
                    if key in queue_url:
                        queue_urls[key] = queue_url

    # Cleanup sqs queues
    sqs_client_primary.purge_queue(QueueUrl=queue_urls["PrimaryQueue"])
    sqs_client_secondary_account.purge_queue(QueueUrl=queue_urls["SecondaryQueue"])

    # Invoke lambda producer primary one
    invoke_result_producer_primary_one = lambda_client_primary.invoke(
        FunctionName=lambda_function_names["ProducerPrimaryOne"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_primary_one["StatusCode"] == 200

    # Invoke lambda producer secondary one
    invoke_result_producer_primary_one = lambda_client_primary.invoke(
        FunctionName=lambda_function_names["ProducerPrimaryTwo"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_primary_one["StatusCode"] == 200

    # Check sqs queue primary for both messages
    messages_primary = sqs_collect_messages(
        sqs_client=sqs_client_primary,
        queue_url=queue_urls["PrimaryQueue"],
        min_events=2,
    )
    for message in messages_primary:
        body = json.loads(message["Body"])
        assert (
            body["source"] == SOURCE_PRODUCER_PRIMARY_ONE
            or body["source"] == SOURCE_PRODUCER_PRIMARY_TWO
        )
        assert body["detail"] == DEFAULT_MESSAGE

    # Invoke lambda producer secondary
    invoke_result_producer_secondary = lambda_client_secondary_account.invoke(
        FunctionName=lambda_function_names["ProducerSecondary"],
        Payload=json.dumps(DEFAULT_MESSAGE),
        InvocationType="RequestResponse",
    )
    assert invoke_result_producer_secondary["StatusCode"] == 200

    # Check sqs queue secondary for fist and third message
    messages_secondary = sqs_collect_messages(
        sqs_client=sqs_client_secondary_account,
        queue_url=queue_urls["SecondaryQueue"],
        min_events=2,  # one from primary region producer one and one from secondary region producer
    )
    for message in messages_secondary:
        body = json.loads(message["Body"])
        assert (
            body["source"] == SOURCE_PRODUCER_PRIMARY_ONE
            or body["source"] == SOURCE_PRODUCER_SECONDARY
        )
        assert body["detail"] == DEFAULT_MESSAGE
