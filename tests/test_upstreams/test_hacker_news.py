from unittest.mock import MagicMock, patch

import pytest

from rumor.exceptions import UpstreamError
from rumor.upstreams.hacker_news import (get_news_items,
                                         news_item_source_request)


@patch('rumor.upstreams.hacker_news.requests')
def test_get_news_items_ok(mock_requests):
    mock_response = MagicMock()
    mock_response.json.return_value = [1, 13, 24]
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    target_api_url = 'https://some-url'

    results = get_news_items(target_api_url)

    assert results == [1, 13, 24]
    mock_requests.get.assert_called_once_with(f'{target_api_url}/v0/topstories.json')


@patch('rumor.upstreams.hacker_news.requests')
def test_get_news_items_error(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests.get.return_value = mock_response

    target_api_url = 'https://some-url'

    with pytest.raises(UpstreamError):
        get_news_items(target_api_url)

    mock_requests.get.assert_called_once_with(f'{target_api_url}/v0/topstories.json')


@patch('rumor.upstreams.hacker_news.requests')
def test_news_item_source_request_ok(mock_requests):
    mock_response = MagicMock()
    mock_response.json.return_value = {'foo': 'bar'}
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    news_item_id = '4753'
    target_api_url = 'https://some-url'

    results = news_item_source_request(news_item_id, target_api_url)

    assert results == {'foo': 'bar'}
    mock_requests.get.assert_called_once_with(f'{target_api_url}/v0/item/{news_item_id}.json')


@patch('rumor.upstreams.hacker_news.requests')
def test_news_item_source_request_error(mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests.get.return_value = mock_response

    news_item_id = '4753'
    target_api_url = 'https://some-url'

    with pytest.raises(UpstreamError):
        news_item_source_request(news_item_id, target_api_url)

    mock_requests.get.assert_called_once_with(f'{target_api_url}/v0/item/{news_item_id}.json')
