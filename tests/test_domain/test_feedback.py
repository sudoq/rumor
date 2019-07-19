from unittest.mock import ANY, call, patch

from rumor.domain import process_feedback


@patch('rumor.domain.feedback.get_bitlink_clicks')
@patch('rumor.domain.feedback.get_bitlinks')
@patch('rumor.domain.feedback.get_primary_group_guid')
def test_process_feedback_ok(mock_get_primary_group_guid, mock_get_bitlinks,
                             mock_get_bitlink_clicks):
    mock_get_primary_group_guid.return_value = 'guid'
    mock_get_bitlinks.return_value = [{
        'id': str(i)
        } for i in range(3)]
    mock_get_bitlink_clicks.return_value = []

    preference_table_name = 'a_table'
    feedback_period_hours = 24
    feedback_max_age_hours = 720
    bitly_access_token = 'at'

    process_feedback(preference_table_name, feedback_period_hours,
                     feedback_max_age_hours, bitly_access_token)

    mock_get_primary_group_guid.assert_called_once_with(bitly_access_token)
    mock_get_bitlinks.assert_called_once_with('guid', bitly_access_token, created_at_from=ANY)
    mock_get_bitlink_clicks.assert_has_calls([
        call(str(i), bitly_access_token, unit='hour', units=24)
        for i in range(3)
    ])
