.PHONY: deploy-localstack deploy-aws

list-resources-localstack:
	@echo "List resources"
	awslocal s3 ls
	awslocal kinesis list-streams
	awslocal firehose list-delivery-streams
	awslocal redshift describe-clusters

start-localstack:
	@docker ps -f "name=localstack" | grep localstack > /dev/null || (echo "Starting localstack..." && localstack start)

deploy-localstack:
	@echo "Preparing deployment"
	cdklocal bootstrap aws://000000000000/us-east-1
	cdklocal bootstrap aws://000000000000/eu-central-1
	AWS_ACCESS_KEY_ID=000000000001 AWS_SECRET_ACCESS_KEY=000000000001 cdklocal bootstrap aws://000000000001/us-east-1
	cdklocal synth
	@echo "Deploy event brdige microservice stack primary region/account"
	cdklocal deploy EventsStackPrimary --require-approval never
	@echo "Deploy event brdige microservice stack secondary region/account"
	cdklocal deploy EventsStackSecondaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary account"
	cdklocal deploy EventsStackSecondaryAccount --require-approval never
	AWS_ACCESS_KEY_ID=000000000001 AWS_SECRET_ACCESS_KEY=000000000001 cdklocal deploy EventsStackSecondaryAccount --require-approval never

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
