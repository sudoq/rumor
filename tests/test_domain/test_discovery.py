from unittest.mock import patch

from rumor.domain import discover


@patch('rumor.domain.discovery.send_messages')
@patch('rumor.domain.discovery.get_news_items')
def test_discover_ok(mock_get_news_items, mock_send_messages):
    mock_get_news_items.return_value = [3, 42, 4753, 5, 7]
    target_api_url = 'https://hacker-news.firebaseio.com'
    queue_name = 'TestQueue'

    discover(limit=3, queue_name=queue_name,
             target_api_url=target_api_url)

    mock_get_news_items.assert_called_once_with(target_api_url)

    expected_entries = [{
        'news_item_id': f'{news_item_id}'
    } for i, news_item_id in enumerate([3, 42, 4753])]
    mock_send_messages.assert_called_once_with(expected_entries, queue_name)
