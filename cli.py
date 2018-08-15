#!/usr/bin/env python3
import json
import os
import random
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

import boto3
import boto3.dynamodb.types
import click
from jinja2 import Template

AVAILABLE_SERVICES = [
    'classification',
    'discovery',
    'evaluation',
    'inspection',
    'report'
]


@click.group()
def cli():
    pass


@cli.group()
def create():
    pass


@cli.group()
def delete():
    pass


@cli.group()
def get():
    pass


@cli.group()
def build():
    pass


@cli.group()
def run():
    pass


def tag_option(func):
    return click.option('--tag', default='latest', type=str)(func)


def prefix_option(func):
    return click.option('--prefix', default='', type=str)(func)


def suffix_option(func):
    return click.option('--suffix', default='', type=str)(func)


def dry_run(func):
    return click.option('--dry-run', is_flag=True, default=False)(func)


def verbose(func):
    return click.option('--verbose', '-v', is_flag=True, default=False)(func)


def quiet(func):
    return click.option('--quiet', '-q', is_flag=True, default=False)(func)


def std_options(func):
    return quiet(verbose(dry_run(func)))


def docker_options(func):
    return suffix_option(prefix_option(tag_option(func)))


@create.command(name='subscription')
@std_options
@click.option('--topic-hint', default='rumor-production-notification-topic')
@click.argument('email')
def create_subscription(email: str, topic_hint: str,
                        dry_run: bool, verbose: bool, quiet: bool):
    client = boto3.client('sns')
    topics = client.list_topics()['Topics']
    topic = _get_topic_arn(topics, topic_hint)
    if dry_run:
        click.echo(f'DRY RUN: Subscribe "{email}" to topic "{topic}"')
        return
    response = client.subscribe(
        TopicArn=topic,
        Protocol='email',
        Endpoint=email,
        ReturnSubscriptionArn=True
    )
    subscription_arn = response['SubscriptionArn']
    if not quiet:
        click.echo(f'Created subscription "{subscription_arn}"')


@create.command(name='keyword')
@std_options
@click.option('--table', default='rumor-production-preferences')
@click.option('--weight', default=1.25, type=float)
@click.argument('keyword')
def create_keyword(keyword: str, weight: int, table: str,
                   dry_run: bool, verbose: bool, quiet: bool):
    preference_item = {
        'preference_type': 'KEYWORD',
        'preference_key': keyword,
        'preference_weight': Decimal(weight)
    }
    _store_preference(preference_item, table)
    click.echo(f'Keyword "{keyword}" with weight {weight} saved to table "{table}"')


@get.command(name='keywords')
@std_options
@click.option('--table', default='rumor-production-preferences')
def get_keywords(table: str, dry_run: bool, verbose: bool, quiet: bool):
    preferences = get_preferences(table)
    for preference in preferences:
        keyword = preference['preference_key']
        weight = preference['preference_weight']
        click.echo(f'{keyword}={weight}')


def get_preferences(preference_table_name: str):
    client = boto3.client('dynamodb')
    paginator = client.get_paginator('query')
    operation_parameters = {
        'TableName': preference_table_name,
        'KeyConditionExpression': 'preference_type = :preference_type',
        'ExpressionAttributeValues': {
            ':preference_type': {'S': 'KEYWORD'}
        }
    }
    items = []
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    page_iterator = paginator.paginate(**operation_parameters)
    for page in page_iterator:
        for item in page['Items']:
            items.append(deserializer.deserialize({'M': item}))

    click.echo('Found {} keywords'.format(len(items)))
    return items


@build.command(name='experiment')
@std_options
@docker_options
@click.argument('experiment_name')
def build_experiment(experiment_name: str, tag: str, prefix: str, suffix: str,
                     dry_run: bool, verbose: bool, quiet: bool):
    if quiet:
        verbose = False
    if verbose:
        click.echo(f'Building experiment: {experiment_name}')

    experiment_path = os.path.join('chaos_experiments', experiment_name)
    if not os.path.isdir(experiment_path):
        if not quiet:
            click.echo(f'Error: {experiment_name}: No such directory')
        return

    image_name = f'{prefix}{experiment_name}{suffix}:{tag}'
    cmd = f'docker build {experiment_path} -t {image_name}'

    if verbose:
        click.echo(f'Running command: "{cmd}"')
    rc, out, err = _run_cmd(cmd, dry_run=dry_run, verbose=verbose, quiet=quiet)
    if rc != 0:
        if not quiet:
            click.echo(err)
            click.echo(f'Error: Command "{cmd}" returned non-zero code {rc}')
        return

    if not quiet:
        click.echo(out)


@run.command(name='experiment')
@std_options
@docker_options
@click.argument('experiment_name')
def run_experiment(experiment_name: str, tag: str, prefix: str, suffix: str,
                   dry_run: bool, verbose: bool, quiet: bool):

    if quiet:
        verbose = False
    if verbose:
        click.echo(f'Running experiment: {experiment_name}')

    experiment_path = os.path.join('chaos_experiments', experiment_name)

    _experiment_exists(experiment_path, quiet=quiet)

    image_name = f'{prefix}{experiment_name}{suffix}:{tag}'
    home_dir = os.environ['HOME']
    pwd = os.environ['PWD']
    volumes = ' -v '.join([
        f"{home_dir}/.aws:/root/.aws",
        f"{pwd}/{experiment_path}:/experiment/output"
    ])
    random_number = random.randint(1, 1000)
    container_name = f'{experiment_name}-{random_number}'
    cmd = (f'docker run -d --rm --name {container_name} '
           f'-v {volumes} {image_name} '
           'chaos --log-file=./output/chaostoolkit.log '
           'run --journal-path=./output/journal.json experiment.json')

    if verbose:
        click.echo(f'Running command: "{cmd}"')

    rc, out, err = _run_cmd(cmd, dry_run=dry_run, verbose=verbose, quiet=quiet)
    if rc != 0:
        if not quiet:
            click.echo(err)
            click.echo(f'Error: Command "{cmd}" returned non-zero code {rc}')
        return

    if not quiet:
        click.echo((f'Container "{container_name}" created\n\n'
                    f'Run following to follow logs:\n\n'
                    f'docker logs -f {container_name}\n'))


@create.command(name='experiment-report')
@std_options
@click.argument('experiment_name')
def create_experiment_report(experiment_name: str, dry_run: bool,
                             verbose: bool, quiet: bool):
    experiment_path = os.path.join('chaos_experiments', experiment_name)
    _experiment_exists(experiment_path, quiet=quiet)

    journal_path = os.path.join(experiment_path, 'journal.json')
    if not os.path.exists(journal_path):
        click.echo(f'No journal.json found for experiment "{experiment_name}"')
        raise click.Abort()

    with open(journal_path) as f:
        journal = json.loads(f.read())

    markdown = _create_experiment_report(journal)

    report_path = os.path.join(experiment_path, 'experiment_report.md')
    with open(report_path, 'w') as f:
        f.write(markdown)

    if not quiet:
        click.echo(f'Experiment report written to "{report_path}"')


def _create_experiment_report(journal: Dict[str, Any]):
    with open(os.path.join('templates', 'experiment_report.md.j2')) as f:
        template = Template(f.read())

    journal.update({
        'formated': {
            'start': datetime.strptime(journal['start'], '%Y-%m-%dT%H:%M:%S.%f'),
            'end': datetime.strptime(journal['end'], '%Y-%m-%dT%H:%M:%S.%f'),
            'duration': timedelta(seconds=journal['duration']),
            'num_probes': len([m for m in journal['experiment']['method'] if m['type'] == 'probe']),
            'num_actions': len([m for m in journal['experiment']['method'] if m['type'] == 'action'])
        }
    }
    )
    return template.render(**journal)


@get.command(name='experiments')
def get_experiments():
    experiments_dir = 'chaos_experiments'
    experiment_names = []
    for item in os.listdir(experiments_dir):
        if item == 'templates':
            continue
        if os.path.isdir(os.path.join(experiments_dir, item)):
            experiment_names.append(item)
    click.echo('\n'.join(experiment_names))


def _run_cmd(cmd: str, dry_run: bool = False,
             verbose: bool = False, quiet: bool = False):
    if dry_run:
        if not quiet:
            click.echo(f'DRY RUN: "{cmd}"')
        return 0, '', ''
    result = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rc = result.returncode
    out = result.stdout.decode('utf-8')
    err = result.stderr.decode('utf-8')
    return rc, out, err


def _experiment_exists(name: str, quiet: bool = False):
    if os.path.isdir(name):
        return True
    if not quiet:
        click.echo(f'Error: {name}: No such directory')
    raise click.Abort()


def _get_topic_arn(topics: List[Dict[str, Any]], topic_arn_hint: str) -> str:
    for topic in topics:
        if topic_arn_hint in topic['TopicArn']:
            return topic['TopicArn']


def _store_preference(preference_item: Dict[str, Any],
                      preference_table_name: str) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(preference_table_name)
    table.put_item(Item=preference_item)


if __name__ == "__main__":
    cli()
