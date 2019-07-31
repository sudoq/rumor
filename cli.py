#!/usr/bin/env python3
from typing import Any, Dict, List

import boto3
import boto3.dynamodb.types
import click

from rumor.upstreams.aws import get_preferences, store_preference

FUNCTION_NAMES = [
    'discovery',
    'inspection',
    'classification',
    'evaluation',
    'report',
    'feedback'
]


@click.group()
def cli():
    pass


@cli.group()
def create():
    pass


@cli.group()
def get():
    pass


def dry_run(func):
    return click.option('--dry-run', is_flag=True, default=False)(func)


def verbose(func):
    return click.option('--verbose', '-v', is_flag=True, default=False)(func)


def quiet(func):
    return click.option('--quiet', '-q', is_flag=True, default=False)(func)


def std_options(func):
    return quiet(verbose(dry_run(func)))


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
def create_keyword(keyword: str, weight: float, table: str,
                   dry_run: bool, verbose: bool, quiet: bool):
    store_preference(keyword, weight, table)
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


def _get_topic_arn(topics: List[Dict[str, Any]], topic_arn_hint: str) -> str:
    for topic in topics:
        if topic_arn_hint in topic['TopicArn']:
            return topic['TopicArn']


if __name__ == "__main__":
    cli()
