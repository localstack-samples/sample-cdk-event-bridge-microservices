.PHONY: deploy-localstack deploy-aws

deploy-localstack:
	@echo "Preparing deployment"
	cdklocal bootstrap
	cdklocal synth
	@echo "Deploy event brdige microservice stack primary region/account"
	cdklocal deploy EventsStackPrimaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary region/account"
	cdklocal deploy EventsStackSecondaryRegion --require-approval never

list-resources-localstack:
	@echo "List resources"
	awslocal s3 ls
	awslocal kinesis list-streams
	awslocal firehose list-delivery-streams
	awslocal redshift describe-clusters

deploy-aws:
	@echo "Preparing deployment"
	cdk bootstrap
	cdk synth
	@echo "Deploy event brdige microservice stack primary region/account"
	cdk deploy EventsStackPrimaryRegion --require-approval never
	@echo "Deploy event brdige microservice stack secondary region/account"
	cdk deploy EventsStackSecondaryRegion --require-approval never

start-localstack:
	@docker ps -f "name=localstack" | grep localstack > /dev/null || (echo "Starting localstack..." && localstack start)

test:
	pytest -v