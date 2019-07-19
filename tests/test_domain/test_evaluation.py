from operator import itemgetter
from unittest.mock import ANY, call, patch

from rumor.domain import evaluate


@patch('rumor.domain.evaluation.create_feedback_link')
@patch('rumor.domain.evaluation.get_preferences')
@patch('rumor.domain.evaluation.store_item')
@patch('rumor.domain.evaluation.get_news_items')
def test_evaluate_ok(mock_get_news_items, mock_store_item,
                     mock_get_preferences, mock_create_feedback_link):
    news_items = [
        {
            'news_item_id': f'{i}',
            'score': 1000 + i if i % 2 == 0 else 100 + i,
            'keywords': [f'keyword-{i}'],
            'url': f'https://example.com/id/{i}'
        }
        for i in range(5)
    ]
    news_items.append({
        'news_item_id': '1',
        'score': 200,
        'keywords': ['keyword-1'],
        'url': f'https://example.com/id/1'
    })

    preferences = [
        {
            'preference_key': f'keyword-{i}',
            'preference_weight': 1.5,
        }
        for i in range(5) if i % 4 == 0
    ]

    feedback_links = ['https://short.en/'] * 6

    mock_get_news_items.return_value = news_items
    mock_get_preferences.return_value = preferences
    mock_create_feedback_link.side_effect = feedback_links

    news_item_table_name = 'news-items'
    evaluation_report_table_name = 'evaluation-reports'
    preference_table_name = 'preferences'
    news_item_max_age_hours = 24
    evaluation_period_hours = 72
    qualification_threshold = 1.5
    qualification_limit = 10
    bitly_access_token = 'bitly-access-token'

    expected_news_items = []
    for i, ni in enumerate(news_items):
        ni['modified_score'] = ni['score']
        ni['feedback_url'] = 'https://short.en/'
        if i % 4 == 0:
            ni['modified_score'] = ni['score'] * 1.5
            expected_news_items.append(ni)
    expected_news_items = sorted(expected_news_items,
                                 key=itemgetter('modified_score'), reverse=True)

    expected_report = {
        'news_items': expected_news_items,
        'config': ANY,
        'created_at': ANY,
        'version': '1'
    }

    results = evaluate(news_item_table_name=news_item_table_name,
                       preference_table_name=preference_table_name,
                       evaluation_report_table_name=evaluation_report_table_name,
                       news_item_max_age_hours=news_item_max_age_hours,
                       evaluation_period_hours=evaluation_period_hours,
                       qualification_threshold=qualification_threshold,
                       qualification_limit=qualification_limit,
                       bitly_access_token=bitly_access_token)

    assert results == expected_report
    mock_get_news_items.assert_called_once_with(news_item_table_name, ANY, ANY)
    mock_get_preferences.assert_called_once_with(preference_table_name)
    mock_store_item.assert_called_once_with(item=expected_report,
                                            table_name=evaluation_report_table_name)
    calls = [call(ni, bitly_access_token) for ni in expected_news_items]
    mock_create_feedback_link.assert_has_calls(calls)
