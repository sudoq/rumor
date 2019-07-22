import pytest


@pytest.fixture
def bitly_api_url():
    return "https://api-ssl.bitly.com/v4"


@pytest.fixture
def bitly_access_token():
    return 'some-token'


@pytest.fixture
def bitly_group_guid():
    return 'some-group-guid'


@pytest.fixture
def bitly_long_url():
    return 'https://example.com?with=some&query=param'


@pytest.fixture
def bitly_bitlink_id():
    return "bit.ly/abc"


@pytest.fixture
def bitly_bitlink_link(bitly_bitlink_id):
    return f"http://{bitly_bitlink_id}"


@pytest.fixture
def bitly_bitlink_title():
    return "This is the title"


@pytest.fixture
def bitly_bitlink(bitly_bitlink_id, bitly_bitlink_link, bitly_long_url, bitly_bitlink_title):
    return {
        "id": bitly_bitlink_id,
        "link": bitly_bitlink_link,
        "long_url": bitly_long_url,
        "title": bitly_bitlink_title
    }


@pytest.fixture
def bitly_group(bitly_group_guid):
    return {
        'guid': bitly_group_guid,
        'is_active': True,
        'role': 'org-admin'
    }
