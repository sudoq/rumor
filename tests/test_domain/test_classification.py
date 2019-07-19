import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from rumor.domain import classify
from rumor.domain.classification import extract_keywords


@patch('rumor.domain.classification.store_item')
@patch('rumor.domain.classification.delete_messages')
@patch('rumor.domain.classification.get_messages')
class TestClassification:
    def test_classification_ok(self, mock_get, mock_delete, mock_store):
        news_items = [
            {
                'id': f'{i}',
                'url': f'url-{i}',
                'title': 'This is some title',
                'score': i,
                'time': int((datetime.now() - timedelta(hours=1)).timestamp())
            }
            for i in range(5)
        ]
        messages = [
            {'Body': json.dumps(item)} for item in news_items
        ]
        mock_get.return_value = messages

        classification_queue_name = 'classification-queue'
        batch_size = 7
        news_item_max_age_hours = 12
        news_item_table_name = 'news-items-table'

        classify(classification_queue_name=classification_queue_name,
                 batch_size=batch_size,
                 news_item_max_age_hours=news_item_max_age_hours,
                 news_item_table_name=news_item_table_name)

        mock_get.assert_called_once_with(queue_name=classification_queue_name,
                                         batch_size=batch_size)
        mock_delete.assert_called_once_with(messages=messages,
                                            queue_name=classification_queue_name)

    @pytest.mark.parametrize('batch_size', [-1, 0, 11])
    def test_classification_invalid_batch_size(self, mock_get, mock_delete,
                                               mock_store, batch_size):
        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        news_item_table_name = 'news-items-table'

        classify(classification_queue_name=classification_queue_name,
                 batch_size=batch_size,
                 news_item_max_age_hours=news_item_max_age_hours,
                 news_item_table_name=news_item_table_name)

        mock_get.assert_not_called()
        mock_delete.assert_not_called()
        mock_store.assert_not_called()

    def test_classification_no_messages(self, mock_get, mock_delete, mock_store):
        mock_get.return_value = []

        classification_queue_name = 'classification-queue'
        news_item_max_age_hours = 12
        news_item_table_name = 'news-items-table'
        batch_size = 5

        classify(classification_queue_name=classification_queue_name,
                 batch_size=batch_size,
                 news_item_max_age_hours=news_item_max_age_hours,
                 news_item_table_name=news_item_table_name)

        mock_get.assert_called_once_with(queue_name=classification_queue_name,
                                         batch_size=batch_size)
        mock_delete.assert_not_called()
        mock_store.assert_not_called()


@pytest.mark.parametrize('sentence, keywords', [
    ('this is a Keyword', ['keyword']),
    ('(this is a Keyword)', ['keyword']),
    ('this is a (Keyword)', ['keyword']),
    ('this is a #Keyword', ['keyword']),
    ('this is a KEYWORD', ['keyword']),
    ('this is a Keyword.', ['keyword']),
    ('this is a Keyword!?', ['keyword']),
    ('this sentence contains two! Keywords?', ['contains', 'keywords']),
])
def test_extract_keywords(sentence, keywords):
    results = extract_keywords(sentence)
    assert set(results) == set(keywords)
