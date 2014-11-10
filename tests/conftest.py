import pytest
from friendly.silverpop.engage.constants import LIST_VISIBILITY_SHARED
import settings
from friendly.silverpop.engage.api import EngageApi


@pytest.fixture(scope='session')
def engage_api():
    return EngageApi(settings.ENGAGE_USERNAME, settings.ENGAGE_PASSWORD, settings.ENGAGE_URL)


@pytest.fixture(scope='session')
def test_database(engage_api):
    # Fetch all private databases of the account
    databases = engage_api.get_databases(LIST_VISIBILITY_SHARED)

    # Locate our test database
    db = next(iter([db for db in databases if db.id == settings.ENGAGE_DATABASE_ID]), None)
    assert db is not None
    assert 'test' in db.name.lower()
    return db


def random_string(length=16):
    import random
    import string
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))