import pytest
from friendly.silverpop.engage import EngageApi, LIST_VISIBILITY_SHARED, LIST_VISIBILITY_PRIVATE
import settings


@pytest.fixture(scope='session')
def engage_api():
    return EngageApi(settings.ENGAGE_USERNAME, settings.ENGAGE_PASSWORD, settings.ENGAGE_URL)


@pytest.fixture(scope='session')
def test_database(engage_api):
    # Fetch all shared databases of the account
    databases = engage_api.get_databases(LIST_VISIBILITY_PRIVATE)

    # Locate our test database
    db = next(iter([db for db in databases if db.id == settings.ENGAGE_DATABASE_ID]), None)
    assert db is not None
    return db