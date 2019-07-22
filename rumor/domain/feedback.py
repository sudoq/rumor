from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

import pytz
from dateutil.parser import parse as parse_date
from logzero import logger

from rumor.domain.classification import extract_keywords
from rumor.upstreams.aws import get_preferences, store_preference
from rumor.upstreams.bitly import (get_bitlink_clicks, get_bitlinks,
                                   get_primary_group_guid)


def process_feedback(preference_table_name: str, feedback_period_hours: int,
                     feedback_max_age_hours: int, bitly_access_token: str = None) -> None:

    if bitly_access_token is None:
        logger.warning('Bitly access token is None')
        return

    bitlinks = _get_bitlinks(bitly_access_token, feedback_max_age_hours)
    if len(bitlinks) == 0:
        logger.info('Found no bitlinks')
        return
    logger.info('Found {} bitlinks to consider'.format(len(bitlinks)))

    clicked_bitlinks_in_period = _get_clicked_bitlinks_in_period(
            bitly_access_token,
            bitlinks,
            feedback_period_hours)

    if len(clicked_bitlinks_in_period) == 0:
        logger.info('No clicked bitlinks in period')
        return

    logger.info('{} clicked links in period'.format(len(clicked_bitlinks_in_period)))
    _update_preferences(clicked_bitlinks_in_period, preference_table_name)


def _get_bitlinks(bitly_access_token: str, feedback_max_age_hours: int) -> List[Dict[str, Any]]:
    bitly_guid = get_primary_group_guid(bitly_access_token)
    now = datetime.now(tz=pytz.UTC)
    link_max_age_date = now - timedelta(days=feedback_max_age_hours)
    return get_bitlinks(bitly_guid, bitly_access_token, created_at_from=link_max_age_date)


def _get_clicked_bitlinks_in_period(bitly_access_token: str, bitlinks: List[Dict[str, Any]],
                                    feedback_period_hours: int) -> List[Dict[str, Any]]:
    now = datetime.now(tz=pytz.UTC)
    clicked_bitlinks_in_period = []
    max_age_consideration = now - timedelta(hours=feedback_period_hours)
    for bitlink in bitlinks:
        clicks = get_bitlink_clicks(bitlink['id'], bitly_access_token,
                                    unit='hour', units=24)
        for click in clicks:
            if click['clicks'] == 0:
                continue
            if parse_date(click['date']) > max_age_consideration:
                clicked_bitlinks_in_period.append(bitlink)
    return clicked_bitlinks_in_period


def _update_preferences(bitlinks: List[Dict[str, Any]], preference_table_name: str) -> None:
    preferences = get_preferences(preference_table_name)
    keywords_with_weights = {
        pref['preference_key']: pref['preference_weight']
        for pref in preferences
    }
    for bitlink in bitlinks:
        title = bitlink.get('title')
        if title is None:
            logger.warning(f"No title found for bitlink with id \"{bitlink['id']}\"")
            continue

        keywords = extract_keywords(title)
        if not keywords:
            logger.warning(f"No keywords found for bitlink with id \"{bitlink['id']}\"")
            continue
        logger.info(f'Adding {keywords} to preferences')
        for keyword in keywords:
            weight = keywords_with_weights.get(keyword, Decimal(1.0))
            weight += Decimal(0.25)
            store_preference(keyword, weight, preference_table_name)
