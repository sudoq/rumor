from unittest.mock import MagicMock, patch

import pytest

from rumor.exceptions import UpstreamError
from rumor.upstreams.bitly import (create_bitlink, get_bitlink_clicks,
                                   get_bitlinks, get_groups,
                                   get_primary_group_guid)


@patch('rumor.upstreams.bitly.requests')
def test_create_bitlink_ok(mock_requests, bitly_access_token, bitly_bitlink,
                           bitly_long_url, bitly_api_url):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = bitly_bitlink
    mock_requests.request.return_value = mock_response

    bitlink = create_bitlink(bitly_long_url, bitly_access_token)

    assert bitlink == bitly_bitlink
    mock_requests.request.assert_called_once_with(
            'POST', f'{bitly_api_url}/shorten',
            json={"long_url": bitly_long_url},
            headers={'Authorization': f'Bearer {bitly_access_token}'})


@patch('rumor.upstreams.bitly.requests')
def test_create_bitlink_fail(mock_requests, bitly_access_token, bitly_long_url, bitly_api_url):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_requests.request.return_value = mock_response

    with pytest.raises(UpstreamError):
        create_bitlink(bitly_long_url, bitly_access_token)

    mock_requests.request.assert_called_once_with(
            'POST', f'{bitly_api_url}/shorten',
            json={"long_url": bitly_long_url},
            headers={'Authorization': f'Bearer {bitly_access_token}'})


@patch('rumor.upstreams.bitly.requests')
def test_get_bitlinks_ok(mock_requests, bitly_group_guid, bitly_access_token,
                         bitly_bitlink, bitly_api_url):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'links': [bitly_bitlink]}
    mock_requests.request.return_value = mock_response

    bitlinks = get_bitlinks(bitly_group_guid, bitly_access_token)

    assert bitlinks == [bitly_bitlink]
    mock_requests.request.assert_called_once_with(
            'GET', f'{bitly_api_url}/groups/{bitly_group_guid}/bitlinks',
            headers={'Authorization': f'Bearer {bitly_access_token}'},
            json=None)


@patch('rumor.upstreams.bitly.requests')
def test_get_groups_ok(mock_requests, bitly_group, bitly_group_guid,
                       bitly_access_token, bitly_api_url):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'groups': [bitly_group]}
    mock_requests.request.return_value = mock_response

    groups = get_groups(bitly_access_token)

    assert groups == [bitly_group]
    mock_requests.request.assert_called_once_with(
            'GET', f'{bitly_api_url}/groups',
            headers={'Authorization': f'Bearer {bitly_access_token}'},
            json=None)


@patch('rumor.upstreams.bitly.requests')
def test_get_primary_group_guid_ok(mock_requests, bitly_group, bitly_group_guid,
                                   bitly_access_token, bitly_api_url):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'groups': [bitly_group]}
    mock_requests.request.return_value = mock_response

    group_guid = get_primary_group_guid(bitly_access_token)

    assert group_guid == bitly_group_guid
    mock_requests.request.assert_called_once_with(
            'GET', f'{bitly_api_url}/groups',
            headers={'Authorization': f'Bearer {bitly_access_token}'},
            json=None)


@patch('rumor.upstreams.bitly.requests')
def test_get_bitlink_clicks(mock_requests, bitly_access_token, bitly_bitlink,
                            bitly_api_url, bitly_bitlink_id):

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total_clicks": 17,
    }

    mock_requests.request.return_value = mock_response

    clicks = get_bitlink_clicks(bitly_bitlink_id, bitly_access_token)

    assert clicks == 17
    mock_requests.request.assert_called_once_with(
            'GET', f'{bitly_api_url}/bitlinks/{bitly_bitlink_id}/clicks/summary',
            headers={'Authorization': f'Bearer {bitly_access_token}'},
            json=None)
