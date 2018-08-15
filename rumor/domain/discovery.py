from logzero import logger

from rumor.upstreams.aws import send_messages
from rumor.upstreams.hacker_news import get_news_items


def discover(target_api_url: str, limit: int, queue_name: str) -> None:
    response_data = get_news_items(target_api_url)
    messages = [
        {
            'news_item_id': f'{r}'
        } for r in response_data[:limit]
    ]
    send_messages(messages, queue_name)
    logger.info('Sent {} messages on queue {}'.format(len(messages), queue_name))
