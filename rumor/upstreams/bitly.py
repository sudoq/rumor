import requests

from rumor.exceptions import UpstreamError


def create_bitlink(long_url: str, access_token: str):
    body = {'long_url': long_url}
    return _call('POST', '/shorten', access_token, body=body)


def get_bitlinks(group_guid: str, access_token: str):
    return _call('GET', f'/groups/{group_guid}/bitlinks', access_token)['links']


def get_bitlink_clicks(bitlink_id: str, access_token: str):
    response = _call('GET', f'/bitlinks/{bitlink_id}/clicks/summary', access_token)
    return response['total_clicks']


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
    if response.status_code != 200:
        raise UpstreamError()
    return response.json()
