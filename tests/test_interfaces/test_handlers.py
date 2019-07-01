from unittest.mock import patch

from rumor.interfaces.handlers import (classification_handler,
                                       discovery_handler, evaluation_handler,
                                       inspection_handler, report_handler)


@patch('rumor.interfaces.handlers.os')
@patch('rumor.interfaces.handlers.discover')
def test_discovery_handler(mock_discover, mock_os):
    mock_os.environ = {}
    discovery_handler({}, {})
    mock_discover.assert_called_once_with(
        limit=5,
        queue_name='rumor-dev-collection-queue',
        target_api_url='https://hacker-news.firebaseio.com'
    )


@patch('rumor.interfaces.handlers.os')
@patch('rumor.interfaces.handlers.inspect')
def test_inspection_handler(mock_inspect, mock_os):
    mock_os.environ = {}
    inspection_handler({}, {})
    mock_inspect.assert_called_once_with(
        batch_size=2,
        classification_queue_name='rumor-dev-classification-queue',
        collection_queue_name='rumor-dev-collection-queue',
        news_item_max_age_hours=48,
        target_api_url='https://hacker-news.firebaseio.com'
    )


@patch('rumor.interfaces.handlers.os')
@patch('rumor.interfaces.handlers.classify')
def test_classification_handler(mock_classify, mock_os):
    mock_os.environ = {}
    classification_handler({}, {})
    mock_classify.assert_called_once_with(
        batch_size=2,
        classification_queue_name='rumor-dev-classification-queue',
        news_item_max_age_hours=48,
        news_item_table_name='rumor-dev-news-items'
    )


@patch('rumor.interfaces.handlers.os')
@patch('rumor.interfaces.handlers.evaluate')
def test_evaluation_handler(mock_evaluate, mock_os):
    mock_os.environ = {}
    evaluation_handler({}, {})
    mock_evaluate.assert_called_once_with(
        evaluation_period_hours=72,
        evaluation_report_table_name='rumor-dev-evaluation-reports',
        preference_table_name='rumor-dev-preferences',
        news_item_max_age_hours=48,
        news_item_table_name='rumor-dev-news-items',
        qualification_limit=10,
        qualification_threshold=1.5,
        bitly_access_token=None
    )


@patch('rumor.interfaces.handlers.os')
@patch('rumor.interfaces.handlers.send_reports')
def test_report_handler(mock_report, mock_os):
    mock_os.environ = {}
    report_handler({}, {})
    mock_report.assert_called_once_with(
        evaluation_report_table_name='rumor-dev-evaluation-reports',
        report_period_hours=24,
        topic_arn_hint='rumor-dev-notification-topic'
    )
