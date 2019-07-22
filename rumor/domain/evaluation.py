from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from operator import itemgetter
from typing import Any, Dict, List

from logzero import logger

from rumor.upstreams.aws import get_news_items, get_preferences, store_item
from rumor.upstreams.bitly import create_bitlink


def evaluate(news_item_table_name: str,
             evaluation_report_table_name: str,
             preference_table_name: str,
             news_item_max_age_hours: int = 24,
             evaluation_period_hours: int = 72,
             qualification_threshold: float = 1.5,
             qualification_limit: int = 10,
             bitly_access_token: str = None) -> Dict[str, Any]:

    now = datetime.now()
    created_at_to = now - timedelta(hours=news_item_max_age_hours)
    created_at_from = created_at_to - timedelta(hours=evaluation_period_hours)

    news_items = get_news_items(news_item_table_name, created_at_from,
                                created_at_to)
    preferences = get_preferences(preference_table_name)
    qualifying_news_items = perform_news_item_qualification(
        news_items,
        qualification_threshold,
        qualification_limit,
        preferences)

    news_items_with_feedback_links = add_feedback_links(qualifying_news_items,
                                                        bitly_access_token)

    evaluation_report = {
        'created_at': int(now.timestamp()),
        'news_items': news_items_with_feedback_links,
        'config': {
            'RUMOR_NEWS_ITEM_MAX_AGE_HOURS': Decimal(news_item_max_age_hours),
            'RUMOR_EVALUATION_PERIOD_HOURS': Decimal(evaluation_period_hours),
            'RUMOR_QUALIFICATION_THRESHOLD': Decimal(qualification_threshold),
            'RUMOR_QUALIFICATION_LIMIT': Decimal(qualification_limit)
        },
        'version': '1'
    }

    if len(qualifying_news_items) > 0:
        logger.info('Stored report')
        store_item(item=evaluation_report, table_name=evaluation_report_table_name)

    return evaluation_report


def perform_news_item_qualification(news_items: List[Dict[str, Any]],
                                    threshold: float,
                                    limit: int,
                                    preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    highscore_map = create_highscore_map(news_items)
    pruned_news_items = highscore_map.values()

    for news_item in pruned_news_items:
        score_modifier = get_score_modifier(news_item, preferences)
        news_item['modified_score'] = news_item['score'] * score_modifier

    mean_score = calculate_mean(pruned_news_items, 'modified_score')
    score_threshold = mean_score * threshold

    qualifying_news_items = [
        it for it in pruned_news_items if it['modified_score'] >= score_threshold
    ]
    sorted_news_items = sorted(qualifying_news_items,
                               key=itemgetter('modified_score'), reverse=True)
    return sorted_news_items[:limit]


def get_score_modifier(news_item: Dict[str, Any], preferences: Dict[str, Any]) -> int:
    score_modifier = 1
    for preference in preferences:
        keyword = preference['preference_key']
        weight = preference['preference_weight']
        if keyword in news_item.get('keywords', []):
            logger.info((f'Found match for {keyword} in '
                         f'news item {news_item["news_item_id"]}: '
                         f'{news_item["keywords"]}'))
            score_modifier *= weight
    return score_modifier


def mean(numbers: int) -> float:
    return float(sum(numbers)) / max(len(numbers), 1)


def calculate_mean(news_items: List[Dict[str, Any]], attribute: str = 'score') -> float:
    return mean([i[attribute] for i in news_items])


def create_highscore_map(news_items: List[Dict[str, Any]]
                         ) -> Dict[str, Dict[str, Any]]:
    results = OrderedDict()
    for news_item in news_items:
        news_item_id = str(news_item['news_item_id'])
        if news_item_id not in results:
            results[news_item_id] = news_item
        else:
            score = int(news_item['score'])
            if score > results[news_item_id]['score']:
                results[news_item_id] = news_item
    return results


def add_feedback_links(news_items: List[Dict[str, Any]],
                       bitly_access_token: str) -> List[Dict[str, Any]]:
    for ni in news_items:
        ni['feedback_url'] = create_feedback_link(ni, bitly_access_token)
    return news_items


def create_feedback_link(news_item: Dict[str, Any], bitly_access_token: str) -> str:
    bitlink = create_bitlink(news_item['url'], news_item['title'], bitly_access_token)
    return bitlink['link']
