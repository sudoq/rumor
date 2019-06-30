from unittest.mock import MagicMock, patch

import pytest

from rumor.exceptions import UpstreamError
from rumor.upstreams.bitly import create_bitlink


@patch('rumor.upstreams.bitly.requests')
def test_create_bitlink_ok(mock_requests):
    long_url = "https://example.com?with=some&query=param"
    access_token = "some-access-token"
    mock_bitlink = {
            "id": "bit.ly/abc",
            "link": "http://bit.ly/abc",
            "long_url": long_url
            }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_bitlink
    mock_requests.post.return_value = mock_response

    bitlink = create_bitlink(long_url, access_token)

    assert bitlink == mock_bitlink
    mock_requests.post.assert_called_once_with(
            "https://api-ssl.bitly.com/v4/shorten",
            json={"long_url": long_url},
            headers={'Authorization': access_token})


@patch('rumor.upstreams.bitly.requests')
def test_create_bitlink_fail(mock_requests):
    long_url = "https://example.com?with=some&query=param"
    access_token = "some-access-token"

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests.post.return_value = mock_response

    with pytest.raises(UpstreamError):
        create_bitlink(long_url, access_token)

    mock_requests.post.assert_called_once_with(
            "https://api-ssl.bitly.com/v4/shorten",
            json={"long_url": long_url},
            headers={'Authorization': access_token})
