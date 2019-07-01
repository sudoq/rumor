import os
from typing import Any, Dict

from rumor.domain import classify, discover, evaluate, inspect, send_reports


def discovery_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    target_api_url = event.get('target_api_url', os.environ.get(
        'RUMOR_DISCOVERY_TARGET_API_URL', 'https://hacker-news.firebaseio.com'
    ))
    limit = event.get('limit', int(os.environ.get('RUMOR_DISCOVERY_LIMIT', '5')))
    queue_name = event.get('queue_name', os.environ.get(
        'RUMOR_COLLECTION_QUEUE_NAME', 'rumor-dev-collection-queue'))

    discover(target_api_url=target_api_url,
             limit=limit,
             queue_name=queue_name)


def inspection_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    collection_queue_name = event.get('queue_name', os.environ.get(
        'RUMOR_COLLECTION_QUEUE_NAME', 'rumor-dev-collection-queue'))
    classification_queue_name = event.get('queue_name', os.environ.get(
        'RUMOR_CLASSIFICATION_QUEUE_NAME', 'rumor-dev-classification-queue'))
    batch_size = event.get('batch_size', int(os.environ.get(
        'RUMOR_INSPECTION_BATCH_SIZE', '2')))
    news_item_max_age_hours = event.get(
        'news_item_max_age_hours', int(os.environ.get(
            'RUMOR_NEWS_ITEM_MAX_AGE_HOURS', '48')))
    target_api_url = event.get('target_api_url', os.environ.get(
        'RUMOR_DISCOVERY_TARGET_API_URL', 'https://hacker-news.firebaseio.com'
    ))

    inspect(collection_queue_name=collection_queue_name,
            classification_queue_name=classification_queue_name,
            batch_size=batch_size,
            news_item_max_age_hours=news_item_max_age_hours,
            target_api_url=target_api_url)


def classification_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    classification_queue_name = event.get('classification_queue_name', os.environ.get(
        'RUMOR_CLASSIFICATION_QUEUE_NAME', 'rumor-dev-classification-queue'))
    batch_size = event.get('batch_size', int(os.environ.get(
        'RUMOR_CLASSIFICATION_BATCH_SIZE', '2')))
    news_item_table_name = event.get(
        'news_item_table_name', os.environ.get(
            'RUMOR_NEWS_ITEM_TABLE_NAME', 'rumor-dev-news-items'))
    news_item_max_age_hours = event.get(
        'news_item_max_age_hours', int(os.environ.get(
            'RUMOR_NEWS_ITEM_MAX_AGE_HOURS', '48')))
    classify(classification_queue_name=classification_queue_name,
             batch_size=batch_size,
             news_item_max_age_hours=news_item_max_age_hours,
             news_item_table_name=news_item_table_name)


def evaluation_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    news_item_max_age_hours = event.get(
        'news_item_max_age_hours', int(os.environ.get(
            'RUMOR_NEWS_ITEM_MAX_AGE_HOURS', '48')))
    evaluation_period_hours = event.get(
        'evaluation_period_hours', int(os.environ.get(
            'RUMOR_EVALUATION_PERIOD_HOURS', '72')))
    qualification_threshold = event.get(
        'qualification_threshold', float(os.environ.get(
            'RUMOR_QUALIFICATION_THRESHOLD', '1.5')))
    qualification_limit = event.get(
        'qualification_limit', int(os.environ.get(
            'RUMOR_QUALIFICATION_LIMIT', '10')))
    news_item_table_name = event.get(
        'news_item_table_name', os.environ.get(
            'RUMOR_NEWS_ITEM_TABLE_NAME', 'rumor-dev-news-items'))
    evaluation_report_table_name = event.get(
        'evaluation_report_table_name', os.environ.get(
            'RUMOR_EVALUATION_REPORT_TABLE_NAME', 'rumor-dev-evaluation-reports'))
    preference_table_name = event.get(
        'preference_table_name', os.environ.get(
            'RUMOR_PREFERENCE_TABLE_NAME', 'rumor-dev-preferences'))
    bitly_access_token = event.get(
        'bitly_access_token', os.environ.get('RUMOR_BITLY_ACCESS_TOKEN'))

    evaluate(news_item_max_age_hours=news_item_max_age_hours,
             evaluation_period_hours=evaluation_period_hours,
             qualification_threshold=qualification_threshold,
             qualification_limit=qualification_limit,
             news_item_table_name=news_item_table_name,
             evaluation_report_table_name=evaluation_report_table_name,
             preference_table_name=preference_table_name,
             bitly_access_token=bitly_access_token)


def report_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    report_period_hours = event.get('report_period_hours', int(os.environ.get(
        'RUMOR_REPORT_PERIOD_HOURS', '24')))
    evaluation_report_table_name = event.get(
        'evaluation_report_table_name', os.environ.get(
            'RUMOR_EVALUATION_REPORT_TABLE_NAME', 'rumor-dev-evaluation-reports'))
    topic_arn_hint = event.get('topic_arn_hint', os.environ.get(
        'RUMOR_NOTIFICATION_TOPIC_NAME', 'rumor-dev-notification-topic'))

    send_reports(report_period_hours=report_period_hours,
                 evaluation_report_table_name=evaluation_report_table_name,
                 topic_arn_hint=topic_arn_hint)
