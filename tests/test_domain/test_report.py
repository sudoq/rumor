from datetime import datetime
from unittest.mock import ANY, patch

from rumor.domain import send_reports


@patch('rumor.domain.report.send_notification')
@patch('rumor.domain.report.get_reports')
class TestReport:
    def test_send_report_ok(self, mock_get_reports, mock_send_notification):
        mock_report = {
            'created_at': int(datetime.now().timestamp()),
            'news_items': [
                {
                    'url': f'some-url-{i}',
                    'score': i,
                    'title': f'title-{i}',
                    'feedback_url': f'some-feedback-url-{i}'
                } for i in range(3)
            ]
        }
        mock_get_reports.return_value = [mock_report]

        report_period_hours = 24
        evaluation_report_table_name = 'evaluation-reports'
        topic_arn_hint = 'topic-hint'

        send_reports(report_period_hours=report_period_hours,
                     evaluation_report_table_name=evaluation_report_table_name,
                     topic_arn_hint=topic_arn_hint)

        mock_get_reports.assert_called_once_with(evaluation_report_table_name, ANY, ANY)
        mock_send_notification.assert_called_once_with(ANY, topic_arn_hint, 'Rumor Report')

    def test_send_report_no_reports(self, mock_get_reports, mock_send_notification):
        mock_get_reports.return_value = []

        report_period_hours = 24
        evaluation_report_table_name = 'evaluation-reports'
        topic_arn_hint = 'topic-hint'

        send_reports(report_period_hours=report_period_hours,
                     evaluation_report_table_name=evaluation_report_table_name,
                     topic_arn_hint=topic_arn_hint)

        mock_get_reports.assert_called_once_with(evaluation_report_table_name, ANY, ANY)
        mock_send_notification.assert_not_called()
