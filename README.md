# CDK deployment of Sample Microservice System of Lambda Functions connected via multiple EventBridge Buses
LocalStack sample CDK app deploying cross-region and cross-account EventBridge buses and Lambda functions connected to them.

| Key          | Value                                                                                                |
| ------------ | ---------------------------------------------------------------------------------------------------- |
| Environment  | <img src="https://img.shields.io/badge/LocalStack-deploys-4D29B4.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAKgAAACoABZrFArwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAALbSURBVHic7ZpNaxNRFIafczNTGIq0G2M7pXWRlRv3Lusf8AMFEQT3guDWhX9BcC/uFAr1B4igLgSF4EYDtsuQ3M5GYrTaj3Tmui2SpMnM3PlK3m1uzjnPw8xw50MoaNrttl+r1e4CNRv1jTG/+v3+c8dG8TSilHoAPLZVX0RYWlraUbYaJI2IuLZ7KKUWCisgq8wF5D1A3rF+EQyCYPHo6Ghh3BrP8wb1en3f9izDYlVAp9O5EkXRB8dxxl7QBoNBpLW+7fv+a5vzDIvVU0BELhpjJrmaK2NMw+YsIxunUaTZbLrdbveZ1vpmGvWyTOJToNlsuqurq1vAdWPMeSDzwzhJEh0Bp+FTmifzxBZQBXiIKaAq8BBDQJXgYUoBVYOHKQRUER4mFFBVeJhAQJXh4QwBVYeHMQJmAR5GCJgVeBgiYJbg4T8BswYPp+4GW63WwvLy8hZwLcd5TudvBj3+OFBIeA4PD596nvc1iiIrD21qtdr+ysrKR8cY42itCwUP0Gg0+sC27T5qb2/vMunB/0ipTmZxfN//orW+BCwmrGV6vd63BP9P2j9WxGbxbrd7B3g14fLfwFsROUlzBmNM33XdR6Meuxfp5eg54IYxJvXCx8fHL4F3w36blTdDI4/0WREwMnMBeQ+Qd+YC8h4g78wF5D1A3rEqwBiT6q4ubpRSI+ewuhP0PO/NwcHBExHJZZ8PICI/e73ep7z6zzNPwWP1djhuOp3OfRG5kLROFEXv19fXP49bU6TbYQDa7XZDRF6kUUtEtoFb49YUbh/gOM7YbwqnyG4URQ/PWlQ4ASllNwzDzY2NDX3WwioKmBgeqidgKnioloCp4aE6AmLBQzUExIaH8gtIBA/lFrCTFB7KK2AnDMOrSeGhnAJSg4fyCUgVHsolIHV4KI8AK/BQDgHW4KH4AqzCQwEfiIRheKKUAvjuuu7m2tpakPdMmcYYI1rre0EQ1LPo9w82qyNziMdZ3AAAAABJRU5ErkJggg=="> <img src="https://img.shields.io/badge/AWS-deploys-F29100.svg?logo=amazon">                                                                                  |
| Services     | EventBridge, Lambda, SimpleQueueService                                                           |
| Integrations | CDK                                                                                                  |
| Categories   | EventDriven                                                                                          |
| Level        | Intermediate                                                                                         |
| GitHub       | [Repository link](https://github.com/localstack-samples/sample-cdk-event-bridge-microservices)        |


![architecture diagram showing the pipeline including Lambda producers, cross-region / cross-account EventBridge buses and Sqs consumers](architecture-diagram.png)

# Prerequisites

## Required Software
- Python 3.11
- node >16
- Docker
- AWS CLI
- AWS CDK
- LocalStack CLI

<details>
  <summary>if you are on Mac:</summary>

    1. install python@3.11
        
        ```bash
        brew install pyenv
        pyenv install 3.11.0
        ```

    2. install nvm and node >= 16
    
        ```bash
        brew install nvm
        nvm install 20
        nvm use 20
        ```
    3. install docker

        ```bash
        brew install docker
        ```

    4. install aws cli, cdk

        ```bash
        brew install awscli
        npm install -g aws-cdk
        ```

    5. install localstack-cli and cdklocal
        
        ```bash
        brew install localstack/tap/localstack-cli
        npm install -g aws-cdk-local
        ```
</details>


## Setup development environment
Clone the repository and navigate to the project directory.
    
```bash
git@github.com:localstack-samples/sample-cdk-event-bridge-microservices.git
cd sample-cdk-event-bridge-microservices
```

Copy `.env.example` to `.env` and set the environment variables based on your target environment.
Make sure to setup both accounts you want to deploy to accordingly.



Create a virtualenv using python@3.11 and install all the development dependencies there:

```bash
pyenv local 3.11.0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```    


# Deployment
- Configure the AWS CLI for both accounts
- Set the environment variables in the .env file based on .env.example (if you want to deploy against AWS make sure to set the correct profile names for your aws cli configuration `ACCOUNT_PROFILE_NAME_SECONDARY=<name>` it must be the same as in your `.aws/config` file)

## Deploy the CDK stack
Against AWS

- bootstrapping is required for the first deployment of both accounts and regions

```bash
cdk bootstrap aws://<account-id>/<region> --profile <profile-name>
```

- use the Makefile command `deploy-aws` or run the following commands manually
  
```bash
cdk synth
cdk deploy EventsStackPrimary 
cdk deploy EventsStackSecondaryRegion
cdk deploy EventsStackSecondaryAccount
```

Against LocalStack

- use the Makefile command `deploy-localstack` or run the following commands manually
- You need to bootstrap for the desired region and account each time you start LocalStack

```bash
localstack start
cdklocal synth
cdklocal bootstrap aws://000000000000/us-east-1
cdklocal bootstrap aws://000000000000/eu-central-1
cdklocal bootstrap aws://000000000001/us-east-1
cdklocal deploy EventsStackPrimary --require-approval never
cdklocal deploy EventsStackSecondaryRegion --require-approval never
cdklocal deploy EventsStackSecondaryAccount --require-approval never
```


# Testing

## Run the tests either against AWS or LocalStack
```bash
make test
```

This will run a pytest defined in `tests/test_event_bridge_microservice.py`, there are two tests, one for cross-account and one for cross-region EventBridge buses, make sure that the correct stacks are deployed to the correct regions and accounts.
The tests will trigger the Lambda functions and assert that the data is being sent to the correct SQS queues.

# Contributing
We appreciate your interest in contributing to our project and are always looking for new ways to improve the developer experience.
We welcome feedback, bug reports, and even feature ideas from the community. Please refer to the contributing file for more details on how to get started.
