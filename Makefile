export AWS_ACCESS_KEY_ID ?= test
export AWS_SECRET_ACCESS_KEY ?= test
export AWS_DEFAULT_REGION=us-east-1
SHELL := /bin/bash

.PHONY: deploy-localstack deploy-aws start stop logs

list-resources-localstack:
	@echo "List resources"
	lstk aws s3 ls
	lstk aws kinesis list-streams
	lstk aws firehose list-delivery-streams
	lstk aws redshift describe-clusters

start:		## Start LocalStack
	@test -n "${LOCALSTACK_AUTH_TOKEN}" || (echo "LOCALSTACK_AUTH_TOKEN is not set. Find your token at https://app.localstack.cloud/workspace/auth-token"; exit 1)
	@LOCALSTACK_AUTH_TOKEN=$(LOCALSTACK_AUTH_TOKEN) lstk start

stop:		## Stop LocalStack
	@lstk stop

logs:		## Save the logs in a separate file
	@lstk logs > logs.txt

start-localstack:
	@docker ps -f "name=localstack" | grep localstack > /dev/null || (echo "Starting localstack..." && lstk start)

deploy-localstack:
	@echo "Preparing deployment"
	lstk cdk bootstrap aws://000000000000/us-east-1
	lstk cdk bootstrap aws://000000000000/eu-central-1
	lstk cdk bootstrap aws://000000000001/us-east-1
	lstk cdk synth
	@echo "Deploy event brdige microservice stack primary region/account"
	lstk cdk deploy EventsStackPrimary --require-approval never
	@echo "Deploy event brdige microservice stack secondary region/account"
	lstk cdk deploy EventsStackSecondaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary account"
	lstk cdk deploy EventsStackSecondaryAccount --require-approval never

deploy-aws:
	@echo "Preparing deployment"
	cdk synth
	@echo "Deploy event brdige microservice stack primary region/account"
	cdk deploy EventsStackPrimary --require-approval never
	@echo "Deploy event brdige microservice stack secondary region"
	cdk deploy EventsStackSecondaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary account"
	cdk deploy EventsStackSecondaryAccount --require-approval never --profile secondary

cleanup-aws:
	@echo "Cleaning up deployment"
	cdk destroy EventsStackPrimary --force
	cdk destroy EventsStackSecondaryRegion --force
	cdk destroy EventsStackSecondaryAccount --force --profile secondary
	@echo "Delete S3 buckets"
	aws s3api delete-bucket --bucket eventbridge-secondary-s3-bucket-one
	aws s3api delete-bucket --bucket eventbridge-secondary-s3-bucket-two --profile secondary

test:
	pytest -v
