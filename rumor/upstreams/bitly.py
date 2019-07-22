from datetime import datetime
from urllib.parse import urlencode

import requests
from logzero import logger

from rumor.exceptions import UpstreamError


def create_bitlink(long_url: str, title: str, access_token: str):
    body = {
        'long_url': long_url,
        'title': title
    }
    return _call('POST', '/shorten', access_token, body=body)


def get_bitlinks(group_guid: str, access_token: str,
                 created_at_from: datetime = None):
    query_string = ''
    if created_at_from is not None:
        query_string = '?created_after={}'.format(int(created_at_from.timestamp()))
    return _call('GET', f'/groups/{group_guid}/bitlinks{query_string}', access_token)['links']


def get_bitlink_clicks(bitlink_id: str, access_token: str,
                       unit: str = None, units: int = None):
    query_params = {}
    query_string = ''
    if unit is not None:
        query_params['unit'] = unit
    if units is not None:
        query_params['units'] = units
    if query_params:
        query_string = '?{}'.format(urlencode(query_params))
    endpoint = f'/bitlinks/{bitlink_id}/clicks{query_string}'
    response = _call('GET', endpoint, access_token)
    return response['link_clicks']


def get_groups(access_token: str):
    return _call('GET', '/groups', access_token)['groups']


def get_primary_group_guid(access_token: str):
    groups = get_groups(access_token)
    for group in groups:
        if group.get('role', '') == 'org-admin':
            return group['guid']
    raise UpstreamError()


def _call(method: str, endpoint: str, access_token: str, body: dict = None):
    bitly_api_url = "https://api-ssl.bitly.com/v4"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.request(method.upper(), f'{bitly_api_url}{endpoint}',
                                json=body, headers=headers)
    if response.status_code not in [200, 201]:
        logger.info(response.status_code)
        raise UpstreamError()
    return response.json()
