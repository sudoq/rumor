from datetime import datetime, timedelta
from typing import Any, Dict, List

from logzero import logger

from rumor.upstreams.aws import get_reports, send_notification


def send_reports(report_period_hours: int, evaluation_report_table_name: str,
                 topic_arn_hint: str) -> None:
    created_at_to = datetime.now()
    created_at_from = created_at_to - timedelta(hours=report_period_hours)
    reports = get_reports(evaluation_report_table_name, created_at_from,
                          created_at_to)
    send(reports, topic_arn_hint)


def send(reports: List[Dict[str, Any]], topic_arn_hint: str) -> None:
    if len(reports) == 0:
        logger.info('No reports to send')
        return
    for report in reports:
        formated_report = format_report(report)
        send_notification(formated_report, topic_arn_hint, 'Rumor Report')
    logger.info('Sent {} report(s)'.format(len(reports)))


def format_report(report: Dict[str, Any]) -> str:
    attributes = get_attributes(report)
    head_template = 'Created {created_at_pretty}\n\n'
    body_template = (
        '[{score} + {score_bonus}] {title}\n'
        '{url}\n'
        '\n'
    )
    head = head_template.format(**attributes)
    body = ''
    for news_item in attributes['news_items']:
        body += body_template.format(**news_item)

    formated_report = head + body

    return formated_report


def get_attributes(report: Dict[str, Any]) -> Dict[str, Any]:
    created_at = report['created_at']
    created_at_pretty = datetime.utcfromtimestamp(created_at).strftime(
        '%Y-%m-%d %H:%M:%S+00:00 (UTC)'
    )
    for ni in report['news_items']:
        modified_score = (ni.get('modified_score')
                          if 'modified_score' in ni else ni['score'])
        score_bonus = modified_score - ni['score']
        ni['score_bonus'] = score_bonus
        ni['modified_score'] = modified_score
    return {
        'created_at': created_at,
        'created_at_pretty': created_at_pretty,
        'news_items': report['news_items']
    }
