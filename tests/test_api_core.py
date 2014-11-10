import re
import pytest
from friendly.silverpop.engage.constants import LIST_VISIBILITY_SHARED, EXPORT_TYPE_ALL, EXPORT_FORMAT_CSV, \
    LIST_VISIBILITY_PRIVATE, COLUMN_TYPE_TEXT
from friendly.silverpop.engage.resources import Session, Contact
from friendly.silverpop.engage.api import CONTACT_CREATED_MANUALLY
from friendly.silverpop.engage.exceptions import RecipientAlreadyExistsError, EngageError, ColumnAlreadyExistsError
from friendly.silverpop.helpers import pep_up
import settings


def test_engage_login_and_logout(engage_api):
    assert engage_api.session is None

    engage_api.login()

    assert isinstance(engage_api.session, Session)
    assert hasattr(engage_api.session, 'id')

    engage_api.logout()

    assert engage_api.session is None


def test_engage_get_databases(engage_api):
    engage_api.get_databases(LIST_VISIBILITY_SHARED)
    # @todo


def test_engage_queries(engage_api):
    for query in engage_api.get_queries(LIST_VISIBILITY_SHARED):
        assert query.get_meta_data()


def test_get_contact_lists(engage_api):
    p = re.compile(r'^\<ContactList \'\d+\'\ \'[^\']+\'\>$')
    for contact_list in engage_api.get_contact_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(contact_list)) is not None


def test_get_test_lists(engage_api):
    p = re.compile(r'^\<TestList \'\d+\'\ \'[^\']+\'\>$')
    for test_list in engage_api.get_test_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(test_list)) is not None


def test_get_suppression_lists(engage_api):
    p = re.compile(r'^\<SuppressionList \'\d+\'\ \'[^\']+\'\>$')
    for suppression_list in engage_api.get_suppression_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(suppression_list)) is not None


def test_get_relational_tables(engage_api):
    cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
    for table in engage_api.get_relational_tables(LIST_VISIBILITY_SHARED):
        assert (table.get_meta_data())

        for column in table._columns:
            assert cp.match(repr(column)) is not None


def test_export_list(engage_api):
    EMAIL = 'test@example.com'

    # Add recipient
    try:
        success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))
        assert success is True
    except RecipientAlreadyExistsError:
        pass

    (success, job_id, file_path) = engage_api.export_list(settings.ENGAGE_DATABASE_ID, EXPORT_TYPE_ALL, EXPORT_FORMAT_CSV)
    assert success is True

    # Remove recipient
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, EMAIL)
    assert success is True


def test_add_recipient(engage_api):
    EMAIL = 'test@example.com'

    # Add recipient
    success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))
    assert success is True

    # Remove recipient
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, EMAIL)
    assert success is True


def test_add_existing_recipient(engage_api):
    EMAIL = 'test@example.com'

    # Add recipient
    success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))
    assert success is True

    # Try to add recipient with same email
    with pytest.raises(RecipientAlreadyExistsError) as e:
        engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))

    # Remove recipient
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, EMAIL)
    assert success is True


def test_add_recipient_unknown_column(engage_api):
    contact = {
        'email': 'test@example.com',
        'unknonw_column': 'nok',
    }
    success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY,
                                       contact, update_if_found=True)
    assert success is True


def test_remove_recipient(engage_api):
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, 'test@example.com')
    assert success is True


def test_select_recipient_data_with_invalid_email(engage_api):
    with pytest.raises(EngageError) as e:
        engage_api.select_recipient_data(settings.ENGAGE_DATABASE_ID, 88351415068)
    assert e.value.msg == 'Error Retrieving Recipient: Argument was not a valid email'


def test_select_recipient_data(engage_api):
    EMAIL = 'test@example.com'

    # Add recipient
    success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))
    assert success is True

    # Query recipient's data
    contact = engage_api.select_recipient_data(settings.ENGAGE_DATABASE_ID, EMAIL)
    assert isinstance(contact, Contact)

    assert contact.email == EMAIL

    for p in ('email', 'emailtype', 'from_element', 'in_el', 'lastmodified', 'organization_id', 'recipientid'):
        assert getattr(contact, p) is not None

    # Remove recipient
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, EMAIL)
    assert success is True


def test_update_recipient_data(engage_api):
    EMAIL = 'test@example.com'
    NEW_EMAIL = 'test2@example.com'

    # Add recipient
    success = engage_api.add_recipient(settings.ENGAGE_DATABASE_ID, CONTACT_CREATED_MANUALLY, dict(email=EMAIL))
    assert success is True

    # Update recipient's email
    success = engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email=NEW_EMAIL), old_email=EMAIL)
    assert success is True

    # Remove recipient
    success = engage_api.remove_recipient(settings.ENGAGE_DATABASE_ID, NEW_EMAIL)
    assert success is True


def test_update_recipient_with_recipient_id(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), recipient_id=1)


def test_update_recipient_with_encoded_recipient_id(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), encoded_recipient_id=1)


def test_update_recipient_with_send_autoreply(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), send_autoreply=1)


def test_update_recipient_with_allow_html(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), allow_html=1)


def test_update_recipient_with_visitor_key(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), visitor_key=1)


def test_update_recipient_with_sync_fields(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), sync_fields=1)


def test_update_recipient_with_snooze_settings(engage_api):
    with pytest.raises(NotImplementedError) as e:
        engage_api.update_recipient(settings.ENGAGE_DATABASE_ID, dict(email='test@example.com'), snooze_settings=1)


def test_create_contact_list(engage_api):
    success = engage_api.create_contact_list(settings.ENGAGE_DATABASE_ID, 'Test List', LIST_VISIBILITY_PRIVATE)
    assert success is True


def test_add_list_column_text(engage_api, test_database):
    COLUMN_NAME = 'My Text COLUMN'
    PEPED_COLUMN_NAME = pep_up(COLUMN_NAME)

    # Create column
    try:
        success = engage_api.add_list_column(
            settings.ENGAGE_DATABASE_ID, COLUMN_NAME, COLUMN_TYPE_TEXT, '')
        assert success is True
    except ColumnAlreadyExistsError:
        pass

    # Retrieve database's meta info
    success = engage_api.get_list_meta_data(test_database)
    assert success is True

    # Check for column
    table = test_database._table
    assert PEPED_COLUMN_NAME in table.column_names
    assert (table[PEPED_COLUMN_NAME]).type == COLUMN_TYPE_TEXT
