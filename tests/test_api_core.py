import re
import pytest
import settings
from friendly.silverpop.engage import LIST_VISIBILITY_SHARED, Session, EngageError, Contact


def test_engage_login_and_logout(engage_api):
    assert engage_api._session is None
    assert engage_api.login()
    assert isinstance(engage_api._session, Session)
    assert hasattr(engage_api._session, '_id')
    assert engage_api.logout()
    assert engage_api._session is None


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


def test_select_recipient_data_with_invalid_email(engage_api):
    with pytest.raises(EngageError) as e:
        engage_api.select_recipient_data(settings.ENGAGE_DATABASE_ID, 88351415068)
    assert e.value.msg == 'Error Retrieving Recipient: Argument was not a valid email'


def test_select_recipient_data(engage_api):
    contact = engage_api.select_recipient_data(settings.ENGAGE_DATABASE_ID, 'alineftmslv@gmail.com')
    assert isinstance(contact, Contact)

    for p in ('email', 'emailtype', 'from_element', 'in_el', 'lastmodified', 'organization_id', 'recipientid'):
        assert getattr(contact, p) is not None
