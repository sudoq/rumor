import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

from boto3.dynamodb.conditions import Attr

from rumor.upstreams.aws import (delete_messages, get_messages, get_news_items,
                                 get_preferences, get_reports, send_messages,
                                 send_notification, store_item)


@patch('rumor.upstreams.aws.boto3')
def test_send_messages_ok(mock_boto3):
    mock_sqs_resource = MagicMock()
    mock_sqs_client = MagicMock()
    mock_sqs_queue = MagicMock()
    mock_boto3.resource.return_value = mock_sqs_resource
    mock_boto3.client.return_value = mock_sqs_client
    mock_sqs_resource.get_queue_by_name.return_value = mock_sqs_queue

    messages = [{'id': '1'}, {'id': '2'}]
    queue_name = 'test-queue'
    batch_size = 10

    send_messages(messages, queue_name=queue_name, batch_size=batch_size)

    mock_sqs_resource.get_queue_by_name.assert_called_once_with(QueueName=queue_name)
    expected_entries = [{
            'Id': f'{i}',
            'MessageBody': json.dumps(message)
        } for i, message in enumerate(messages)]
    calls = [call(QueueUrl=mock_sqs_queue.url, Entries=expected_entries)]
    mock_sqs_client.send_message_batch.assert_has_calls(calls)


@patch('rumor.upstreams.aws.boto3')
def test_get_messages_ok(mock_boto3):
    mock_sqs_resource = MagicMock()
    mock_sqs_client = MagicMock()
    mock_sqs_queue = MagicMock()
    mock_boto3.resource.return_value = mock_sqs_resource
    mock_boto3.client.return_value = mock_sqs_client
    mock_sqs_resource.get_queue_by_name.return_value = mock_sqs_queue
    mock_sqs_client.receive_message.return_value = {
        'Messages': [{'foo': '1', 'bar': '2'}]
    }

    queue_name = 'test-queue'
    batch_size = 5

    messages = get_messages(queue_name, batch_size)

    assert messages == [{'foo': '1', 'bar': '2'}]
    mock_sqs_resource.get_queue_by_name.assert_called_once_with(QueueName=queue_name)
    mock_sqs_client.receive_message.assert_called_once_with(
        QueueUrl=mock_sqs_queue.url,
        MaxNumberOfMessages=batch_size,
        WaitTimeSeconds=0)


@patch('rumor.upstreams.aws.boto3')
def test_delete_messages_ok(mock_boto3):
    mock_sqs_resource = MagicMock()
    mock_sqs_client = MagicMock()
    mock_sqs_queue = MagicMock()
    mock_boto3.resource.return_value = mock_sqs_resource
    mock_boto3.client.return_value = mock_sqs_client
    mock_sqs_resource.get_queue_by_name.return_value = mock_sqs_queue

    messages = [
        {'id': 'f{i}', 'ReceiptHandle': f'receipt-handle-{i}'}
        for i in range(2)
    ]
    queue_name = 'test-queue'

    delete_messages(messages, queue_name)

    mock_sqs_resource.get_queue_by_name.assert_called_once_with(QueueName=queue_name)
    calls = [call(QueueUrl=mock_sqs_queue.url, ReceiptHandle=f'receipt-handle-{i}')
             for i in range(2)]
    mock_sqs_client.delete_message.assert_has_calls(calls)


@patch('rumor.upstreams.aws.boto3')
def test_store_item_ok(mock_boto3):
    mock_dynamodb_resource = MagicMock()
    mock_table = MagicMock()
    mock_boto3.resource.return_value = mock_dynamodb_resource
    mock_dynamodb_resource.Table.return_value = mock_table

    item = {'foo': 'bar'}
    table_name = 'test-table'

    store_item(item, table_name)

    mock_boto3.resource.assert_called_once_with('dynamodb')
    mock_dynamodb_resource.Table.assert_called_once_with(table_name)
    mock_table.put_item.assert_called_once_with(Item=item)


@patch('rumor.upstreams.aws.boto3')
def test_get_news_items_ok(mock_boto3):
    news_item_page = [{}]*4

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_deserializer = MagicMock()
    mock_paginator.paginate.return_value = [{'Items': news_item_page}]
    mock_boto3.dynamodb.types.TypeDeserializer.return_value = mock_deserializer

    mock_boto3.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_deserializer.deserialize.side_effect = lambda x: x['M']

    news_item_table_name = 'news-items'
    created_at_to = datetime.now()
    created_at_from = created_at_to - timedelta(days=1)

    results = get_news_items(news_item_table_name, created_at_from, created_at_to)

    assert results == news_item_page * 2

    mock_boto3.client.assert_called_once_with('dynamodb')
    mock_client.get_paginator.assert_called_once_with('query')
    pag_dates = map(str, [created_at_to.date(), created_at_from.date()])
    paginator_calls = [
        call(
            ExpressionAttributeValues={
                ':created_at_date': {'S': pag_date},
                ':ca_from': {'N': str(created_at_from.timestamp())},
                ':ca_to': {'N': str(created_at_to.timestamp())}
            }, IndexName='LSI',
            KeyConditionExpression=('created_at_date = :created_at_date '
                                    'AND created_at BETWEEN '
                                    ':ca_from AND :ca_to'),
            TableName=news_item_table_name
        ) for pag_date in pag_dates
    ]
    mock_paginator.paginate.assert_has_calls(paginator_calls)
    mock_deserializer.deserialize.assert_has_calls(
        [call({'M': {}})]*8
    )


@patch('rumor.upstreams.aws.boto3')
def test_get_preferences(mock_boto3):
    preference_page = [{}]*4

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_deserializer = MagicMock()
    mock_paginator.paginate.return_value = [{'Items': preference_page}]
    mock_boto3.dynamodb.types.TypeDeserializer.return_value = mock_deserializer

    mock_boto3.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_deserializer.deserialize.side_effect = lambda x: x['M']

    preference_table_name = 'preferences'

    results = get_preferences(preference_table_name)

    assert results == preference_page
    mock_boto3.client.assert_called_once_with('dynamodb')
    mock_client.get_paginator.assert_called_once_with('query')
    mock_paginator.paginate.assert_called_once_with(
        TableName=preference_table_name,
        KeyConditionExpression='preference_type = :preference_type',
        ExpressionAttributeValues={
            ':preference_type': {'S': 'KEYWORD'}
        }
    )
    mock_deserializer.deserialize.assert_has_calls(
        [call({'M': {}})]*4
    )


@patch('rumor.upstreams.aws.boto3')
def test_send_notification_ok(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.list_topics.return_value = {
        'Topics': [
            {
                'TopicArn': f'arn:{topic_arn}:id:something'
            } for topic_arn in [
                'notification-topic',
                'another-topic',
                'testing-topic'
            ]
        ]
    }

    msg = 'Test body'
    topic_arn_hint = 'notification-topic'
    subject = 'Test subject'

    send_notification(msg, topic_arn_hint, subject)

    mock_boto3.client.assert_called_once_with('sns')
    mock_client.publish.assert_called_once_with(
        Subject=subject,
        Message=msg,
        TopicArn=f'arn:{topic_arn_hint}:id:something'
    )


@patch('rumor.upstreams.aws.boto3')
def test_get_reports(mock_boto3):
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_boto3.resource.return_value = mock_resource
    mock_resource.Table.return_value = mock_table
    mock_table.scan.return_value = {'Items': [{'foo': 'bar'}]}

    evaluation_report_table_name = 'evaluation-reports'
    created_at_to = datetime.now()
    created_at_from = created_at_to - timedelta(days=1)

    results = get_reports(evaluation_report_table_name, created_at_from,
                          created_at_to)

    assert results == [{'foo': 'bar'}]
    mock_boto3.resource.assert_called_once_with('dynamodb')
    mock_resource.Table.assert_called_once_with(evaluation_report_table_name)
    expected_filter_expression = (
        Attr('created_at').gte(Decimal(created_at_from.timestamp())) &
        Attr('created_at').lt(Decimal(created_at_to.timestamp()))
    )
    mock_table.scan.assert_called_once_with(
        FilterExpression=expected_filter_expression
    )
