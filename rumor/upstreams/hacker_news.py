from typing import Any, Dict, List

import requests
from logzero import logger

from rumor.exceptions import UpstreamError


def get_news_items(target_api_url: str) -> List[int]:
    endpoint = '/v0/topstories'
    api_url = f'{target_api_url}{endpoint}.json'
    response = requests.get(api_url)
    status_code = response.status_code
    if status_code != 200:
        error_msg = f"GET {api_url} returned status code {status_code}"
        logger.info(error_msg)
        raise UpstreamError(error_msg)
    return response.json()


def news_item_source_request(news_item_id: str,
                             target_api_url: str) -> Dict[str, Any]:
    endpoint = f'/v0/item/{news_item_id}'
    api_url = f'{target_api_url}{endpoint}.json'
    response = requests.get(api_url)
    status_code = response.status_code
    if status_code != 200:
        error_msg = f"GET {api_url} returned status code {status_code}"
        logger.info(error_msg)
        raise UpstreamError(error_msg)

    return response.json()
