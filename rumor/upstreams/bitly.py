import requests

from rumor.exceptions import UpstreamError


def create_bitlink(long_url: str, access_token: str):
    bitly_api_url = "https://api-ssl.bitly.com/v4/shorten"
    headers = {'Authorization': access_token}
    body = {'long_url': long_url}
    response = requests.post(bitly_api_url, json=body, headers=headers)
    if response.status_code != 200:
        raise UpstreamError()
    return response.json()
