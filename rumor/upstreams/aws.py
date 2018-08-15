import json
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

import boto3
import boto3.dynamodb.types
from boto3.dynamodb.conditions import Attr
from logzero import logger


def send_messages(messages: List[Dict[str, str]], queue_name: str,
                  batch_size: int = 10) -> None:
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    entries = [{
        'Id': f'{i}',
        'MessageBody': json.dumps(msg)
    } for i, msg in enumerate(messages)]

    num_segments = math.ceil(len(messages)/float(batch_size))
    for k in range(num_segments):
        i = k*batch_size
        j = i+batch_size
        client.send_message_batch(
            QueueUrl=queue.url,
            Entries=entries[i:j]
        )


def get_messages(queue_name: str, batch_size: int = 10) -> List[Dict[str, Any]]:
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    response = client.receive_message(QueueUrl=queue.url,
                                      MaxNumberOfMessages=batch_size,
                                      WaitTimeSeconds=0)
    return response.get('Messages', [])


def delete_messages(messages: List[Dict[str, Any]], queue_name: str):
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    for message in messages:
        client.delete_message(QueueUrl=queue.url,
                              ReceiptHandle=message['ReceiptHandle'])


def store_item(item: Dict[str, Any], table_name: str) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(Item=item)


def get_news_items(news_item_table_name: str, created_at_from: datetime,
                   created_at_to: datetime) -> List[Dict[str, Any]]:
    client = boto3.client('dynamodb')
    paginator = client.get_paginator('query')
    number_of_queries = math.ceil((created_at_to - created_at_from).total_seconds() / 86400.0) + 1
    _now = datetime.now()
    partition_keys = [str((_now - timedelta(days=d)).date()) for d in range(number_of_queries)]
    operation_parameters_list = [{
        'TableName': news_item_table_name,
        'IndexName': 'LSI',
        'KeyConditionExpression': ('created_at_date = :created_at_date AND '
                                   'created_at BETWEEN :ca_from AND :ca_to'),
        'ExpressionAttributeValues': {
            ':created_at_date': {'S': pk},
            ':ca_from': {'N': str(created_at_from.timestamp())},
            ':ca_to': {'N': str(created_at_to.timestamp())},
        }
    } for pk in partition_keys]
    items = []
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    for operation_parameters in operation_parameters_list:
        page_iterator = paginator.paginate(**operation_parameters)
        for page in page_iterator:
            for item in page['Items']:
                items.append(deserializer.deserialize({'M': item}))

    logger.info('Found {} news items to evaluate'.format(len(items)))
    return items


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

    logger.info('Found {} keywords'.format(len(items)))
    return items


def send_notification(msg: str, topic_arn_hint: str, subject: str) -> None:
    client = boto3.client('sns')
    topics = client.list_topics()['Topics']
    topic_arn = get_topic_arn(topics, topic_arn_hint)
    client.publish(
        Subject=subject,
        Message=msg,
        TopicArn=topic_arn
    )


def get_topic_arn(topics: List[Dict[str, Any]], topic_arn_hint: str) -> str:
    for topic in topics:
        if topic_arn_hint in topic['TopicArn']:
            return topic['TopicArn']


def get_reports(evaluation_report_table_name: str, created_at_from: datetime,
                created_at_to: datetime) -> List[Dict[str, Any]]:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(evaluation_report_table_name)

    response = table.scan(
        FilterExpression=(
            Attr('created_at').gte(Decimal(created_at_from.timestamp())) &
            Attr('created_at').lt(Decimal(created_at_to.timestamp()))
        )
    )

    return response['Items']
