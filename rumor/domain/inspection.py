import json
from datetime import datetime, timedelta

from logzero import logger

from rumor.upstreams.aws import delete_messages, get_messages, send_messages
from rumor.upstreams.hacker_news import news_item_source_request


def inspect(collection_queue_name: str,
            classification_queue_name: str, batch_size: int,
            news_item_max_age_hours: int, target_api_url: str):

    if batch_size <= 0 or batch_size > 10:
        logger.warning(f'Invalid batch size: {batch_size}')
        return

    messages = get_messages(queue_name=collection_queue_name, batch_size=batch_size)
    if len(messages) == 0:
        logger.info('Queue is empty')
        return

    classification_messages = []
    for message in messages:
        data = json.loads(message['Body'])
        news_item_data = news_item_source_request(data['news_item_id'], target_api_url)

        if 'url' not in news_item_data:
            continue

        created_at_before_threshold = (
            datetime.now() - timedelta(hours=news_item_max_age_hours)
        ).timestamp()
        if news_item_data['time'] <= created_at_before_threshold:
            continue

        classification_messages.append(news_item_data)

    delete_messages(messages=messages, queue_name=collection_queue_name)

    if len(classification_messages) == 0:
        logger.info('No messages to send')
        return

    send_messages(messages=classification_messages,
                  queue_name=classification_queue_name,
                  batch_size=batch_size)

    logger.info('Read {} messages from queue {}'.format(len(messages),
                                                        collection_queue_name))
    logger.info('Sent {} messages on queue {}'.format(len(classification_messages),
                                                      classification_queue_name))
