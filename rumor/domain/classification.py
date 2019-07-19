import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from logzero import logger

from rumor.upstreams.aws import delete_messages, get_messages, store_item

KEYWORD_PATTERN = re.compile("[a-zA-Z]{2,}")
EXCLUDED_FILES_PATH = 'rumor/files/excluded_words.txt'


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
    news_item['keywords'] = extract_keywords(news_item['title'])
    logger.info(news_item['keywords'])
    return news_item


def extract_keywords(sentence):
    # TODO Note add warning if trying to add excluded word to preferences.
    excluded_words = set(get_excluded_words(EXCLUDED_FILES_PATH))
    words_in_sentence = set(map(str.lower, KEYWORD_PATTERN.findall(sentence)))
    return list(words_in_sentence - excluded_words)


def get_excluded_words(path):
    words = []
    with open(path) as f:
        words = [line.strip() for line in f.readlines()]
    return words


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
