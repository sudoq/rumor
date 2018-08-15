import json
from datetime import datetime, timedelta
from typing import Any, Dict

from logzero import logger

from rumor.upstreams.aws import delete_messages, get_messages, store_item


def classify(classification_queue_name: str, batch_size: int,
             news_item_max_age_hours: int,
             news_item_table_name: str) -> None:

    if batch_size <= 0 or batch_size > 10:
        logger.warning(f'Invalid batch size: {batch_size}')
        return

    messages = get_messages(queue_name=classification_queue_name, batch_size=batch_size)
    if len(messages) == 0:
        logger.info('Queue is empty')
        return

    for message in messages:
        body = json.loads(message['Body'])
        classified_data = classify_news_item(body)
        normalized_data = normalize(classified_data, ttl_hours=news_item_max_age_hours*3)
        store_item(normalized_data, news_item_table_name)

    delete_messages(messages=messages, queue_name=classification_queue_name)

    logger.info('Read {} messages from queue {}'.format(len(messages),
                                                        classification_queue_name))


def classify_news_item(news_item: Dict[str, Any]) -> Dict[str, Any]:
    keywords = []
    for word in news_item['title'].split():
        if word.istitle():
            keywords.append(word.lower())
    news_item['keywords'] = keywords
    return news_item


def normalize(input_data: Dict[str, Any], ttl_hours: int) -> Dict[str, Any]:
    timestamp = int(datetime.now().timestamp())
    created_at = datetime.fromtimestamp(input_data['time'])
    return {
        'news_item_id': str(input_data['id']),
        'score': input_data['score'],
        'url': input_data['url'],
        'title': input_data['title'],
        'created_at_date': str(created_at.date()),
        'created_at': int(created_at.timestamp()),
        'updated_at': timestamp,
        'ttl': timestamp + int(timedelta(hours=ttl_hours).total_seconds()),
        'keywords': input_data['keywords']
    }
