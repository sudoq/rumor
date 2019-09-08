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
[![CircleCI](https://circleci.com/gh/SudoQ/rumor/tree/master.svg?style=svg)](https://circleci.com/gh/SudoQ/rumor/tree/master)
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
$ pip install -r requirements-dev.txt
$ python cli.py --help
```

### Configuration
In order to get the system up and running, you need to store the following information in AWS SSM Parameter Store:
- A target administrator email (Used for receiving CloudWatch alerts)

Before deploying the application you need to configure this parameter with the following command:
```
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

To run a chaos experiment, make sure you have installed the [Chaos Toolkit](https://chaostoolkit.org/) and the Chaos Toolkit AWS extension in a python environment. This can be achived by following the installation steps required for installing the Command-Line Interface `cli.py`, see [Installation](#installation).

All experiments JSON files are located in the `chaos_experiments` directory.

### Example
To run the `discovery_change_memory_size.json` experiment, navigate to the `chaos_experiments` directory and run the following command:

```
$ chaos run discovery_change_memory_size.json
```

This will run the experiments and create journal and log files in the current directory.

For more information about the Chaos Toolkit `chaos` command, run the following command:

```
$ chaos --help
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
