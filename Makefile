export AWS_ACCESS_KEY_ID ?= test
export AWS_SECRET_ACCESS_KEY ?= test
export AWS_DEFAULT_REGION=us-east-1
SHELL := /bin/bash

.PHONY: deploy-localstack deploy-aws start stop ready logs

list-resources-localstack:
	@echo "List resources"
	awslocal s3 ls
	awslocal kinesis list-streams
	awslocal firehose list-delivery-streams
	awslocal redshift describe-clusters

start:		## Start LocalStack
	@test -n "${LOCALSTACK_AUTH_TOKEN}" || (echo "LOCALSTACK_AUTH_TOKEN is not set. Find your token at https://app.localstack.cloud/workspace/auth-token"; exit 1)
	@LOCALSTACK_AUTH_TOKEN=$(LOCALSTACK_AUTH_TOKEN) localstack start -d

stop:		## Stop LocalStack
	@localstack stop

ready:		## Wait until LocalStack is ready
	@echo Waiting on the LocalStack container...
	@localstack wait -t 30 && echo LocalStack is ready to use! || (echo Gave up waiting on LocalStack, exiting. && exit 1)

logs:		## Save the logs in a separate file
	@localstack logs > logs.txt

start-localstack:
	@docker ps -f "name=localstack" | grep localstack > /dev/null || (echo "Starting localstack..." && localstack start)

deploy-localstack:
	@echo "Preparing deployment"
	cdklocal bootstrap aws://000000000000/us-east-1
	cdklocal bootstrap aws://000000000000/eu-central-1
	cdklocal bootstrap aws://000000000001/us-east-1
	cdklocal synth
	@echo "Deploy event brdige microservice stack primary region/account"
	cdklocal deploy EventsStackPrimary --require-approval never
	@echo "Deploy event brdige microservice stack secondary region/account"
	cdklocal deploy EventsStackSecondaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary account"
	cdklocal deploy EventsStackSecondaryAccount --require-approval never

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
