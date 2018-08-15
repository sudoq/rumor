import json
from datetime import datetime, timedelta
from unittest.mock import ANY, patch

import pytest

from rumor.domain import inspect


@patch('rumor.domain.inspection.news_item_source_request')
@patch('rumor.domain.inspection.delete_messages')
@patch('rumor.domain.inspection.send_messages')
@patch('rumor.domain.inspection.get_messages')
class TestInspection:
    def test_inspect_ok(self, mock_get, mock_send,
                        mock_delete, mock_get_news_item):
        messages = [
            {'Body': json.dumps({'news_item_id': f'{i}'})}
            for i in range(5)
        ]
        mock_get.return_value = messages
        mock_get_news_item.side_effect = [
            {
                'url': f'url-{i}',
                'time': int((datetime.now() - timedelta(hours=1)).timestamp())
            }
            for i in range(5)
        ]

        collection_queue_name = 'collection-queue'
        classification_queue_name = 'classification-queue'
        batch_size = 7
        news_item_max_age_hours = 12
        target_api_url = 'https://some-url'

        inspect(collection_queue_name=collection_queue_name,
                classification_queue_name=classification_queue_name,
                batch_size=batch_size,
                news_item_max_age_hours=news_item_max_age_hours,
                target_api_url=target_api_url)

        mock_get.assert_called_once_with(queue_name=collection_queue_name,
                                         batch_size=batch_size)
        mock_send.assert_called_once_with(
            batch_size=7,
            messages=[{
                'url': f'url-{i}',
                'time': ANY
            } for i in range(5)],
            queue_name=classification_queue_name
        )
        mock_delete.assert_called_once_with(messages=messages,
                                            queue_name=collection_queue_name)

    @pytest.mark.parametrize('batch_size', [-1, 0, 11])
    def test_inspect_invalid_batch_size(self, mock_get, mock_send,
                                        mock_delete, mock_get_news_item,
                                        batch_size):
        collection_queue_name = 'collection-queue'
        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        target_api_url = 'https://some-url'

        inspect(collection_queue_name=collection_queue_name,
                classification_queue_name=classification_queue_name,
                batch_size=batch_size,
                news_item_max_age_hours=news_item_max_age_hours,
                target_api_url=target_api_url)

        mock_get.assert_not_called()
        mock_send.assert_not_called()
        mock_delete.assert_not_called()
        mock_get_news_item.assert_not_called()

    def test_inspect_no_messages(self, mock_get, mock_send,
                                 mock_delete, mock_get_news_item):
        mock_get.return_value = []

        collection_queue_name = 'collection-queue'
        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        target_api_url = 'https://some-url'
        batch_size = 5

        inspect(collection_queue_name=collection_queue_name,
                classification_queue_name=classification_queue_name,
                batch_size=batch_size,
                news_item_max_age_hours=news_item_max_age_hours,
                target_api_url=target_api_url)

        mock_get.assert_called_with(queue_name=collection_queue_name,
                                    batch_size=batch_size)
        mock_send.assert_not_called()
        mock_delete.assert_not_called()
        mock_get_news_item.assert_not_called()

    def test_inspect_insufficient_data(self, mock_get, mock_send,
                                       mock_delete, mock_get_news_item):
        messages = [
            {'Body': json.dumps({'news_item_id': '1'})}
        ]
        mock_get.return_value = messages
        mock_get_news_item.return_value = {'id': 1}

        collection_queue_name = 'collection-queue'
        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        target_api_url = 'https://some-url'
        batch_size = 5

        inspect(collection_queue_name=collection_queue_name,
                classification_queue_name=classification_queue_name,
                batch_size=batch_size,
                news_item_max_age_hours=news_item_max_age_hours,
                target_api_url=target_api_url)

        mock_get.assert_called_with(queue_name=collection_queue_name,
                                    batch_size=batch_size)
        mock_get_news_item.assert_called_once_with('1', target_api_url)
        mock_delete.assert_called_with(messages=messages,
                                       queue_name=collection_queue_name)
        mock_send.assert_not_called()

    def test_inspect_old_news_item(self, mock_get, mock_send,
                                   mock_delete, mock_get_news_item):
        messages = [
            {'Body': json.dumps({'news_item_id': '1'})}
        ]
        mock_get.return_value = messages
        mock_get_news_item.return_value = {
            'id': 1,
            'url': 'some-url',
            'time': int(datetime(1970, 1, 1).timestamp())
        }

        collection_queue_name = 'collection-queue'
        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        target_api_url = 'https://some-url'
        batch_size = 5

        inspect(collection_queue_name=collection_queue_name,
                classification_queue_name=classification_queue_name,
                batch_size=batch_size,
                news_item_max_age_hours=news_item_max_age_hours,
                target_api_url=target_api_url)

        mock_get.assert_called_with(queue_name=collection_queue_name,
                                    batch_size=batch_size)
        mock_get_news_item.assert_called_once_with('1', target_api_url)
        mock_delete.assert_called_with(messages=messages,
                                       queue_name=collection_queue_name)
        mock_send.assert_not_called()
