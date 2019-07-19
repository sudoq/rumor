# Rumor
Algorithmically curated technology newsletters.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Chaos Experiments](#chaos-experiments)
- [Contributing](#contributing)
- [License](#license)

## Introduction
[![CI status](https://travis-ci.com/SudoQ/rumor.svg?branch=master)](https://travis-ci.com/SudoQ/rumor)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Rumor is an email newsletter subscription service that periodically sends an algorithmically curated newsletter based on news items posted on the social news website [Hacker News](https://news.ycombinator.com/).

## Features
* An email newsletter subscription service that provides relevant news stories based on configurable keyword preferences.
* Cheap to operate. Runs on [AWS always-free tier](https://aws.amazon.com/free/?awsf.Free%20Tier%20Types=categories%23alwaysfree).
* Embraces infrastructure-as-code. The full AWS environment is deployable with [CloudFormation](https://aws.amazon.com/cloudformation/) using the [Serverless Framework](https://serverless.com/).
* Application monitoring and alerting. Includes preconfigured [AWS CloudWatch](https://aws.amazon.com/cloudwatch/) dashboards and alerts.
* Reliable. Includes [chaos experiments](https://principlesofchaos.org/) to explore the resilience of the system.

## Installation

### Requirements
* AWS Account
* Docker
* Node.js
* Linux or OSX
* Python 3.6+

Make sure the `serverless` CLI tool and an AWS account is setup correctly by following the installation instructions available [here](https://serverless.com/framework/docs/providers/aws/guide/installation/).

To use the Command-Line Interface, create a python virtual environment and install the required dependencies.
```
$ virtualenv venv -p python3
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python cli.py --help
```

### Configuration
In order to get the system up and running, you need to store the following information in AWS SSM Parameter Store:
- An target administrator email (Used for receiving CloudWatch alerts)
- Bitly access token (Used for generating bitly links)

Before deploying the application you need to configure these parameters with the following commands:
```
aws ssm put-parameter --name rumorBitlyAccessToken --type String --value myBitlyAccessToken
aws ssm put-parameter --name rumorAdminEmail --type String --value foobar@example.com
```

## Usage
### Serverless framework
Run the following command to deploy the production environment.
```
serverless deploy
```

### Command-Line Interface

Create a newsletter email subscription for `foobar@example.com`.
```
$ python cli.py create subscription foobar@example.com
```

Add a keyword preference `serverless` with weight `2.5`.
```
$ python cli.py create keyword serverless --weight 2.5
```

## Chaos Experiments

The following section describes how to setup and run Chaos Experiments.

Setup the python environment required for the Command-Line Interface `cli.py`, see [Installation](#installation), and make sure Docker is running as the experiments are built and executed using Docker.

List all chaos experiments
```
$ python cli.py get experiments
```

Build and run the `discovery_reduce_memory_size` experiment. The experiment will invoke the `discovery` lambda function with reduced memory size settings.
```
$ python cli.py build experiment discovery_reduce_memory_size
$ python cli.py run experiment discovery_reduce_memory_size
```

To generate a markdown report of the conducted experiment, run the following command.
```
$ python cli.py create experiment-report discovery_reduce_memory_size
```

The [Chaos Toolkit](https://chaostoolkit.org/) is used to setup and run the experiments.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
