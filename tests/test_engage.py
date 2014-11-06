# -*- coding: utf-8 -*-

import nose
import re
import datetime
from friendly.silverpop.engage import Session, LIST_VISIBILITY_SHARED, Table, Column, Contact, COLUMN_TYPE_TEXT


def test_table_definition():
    table = Table()

    table.add_column(Column('email', COLUMN_TYPE_TEXT, None, is_key=True))
    assert table.has_column('email') is True
    assert 'email' in table.key_columns

    table.add_column(Column('firstname', COLUMN_TYPE_TEXT))
    assert table.has_column('firstname')
    assert not 'firstname' in table.key_columns

    table.add_column(Column('lastname', COLUMN_TYPE_TEXT))
    assert table.has_column('lastname')
    assert not 'lastname' in table.key_columns


def test_access_to_invalid_attribute_on_contact():
    table = Table()

    contact = Contact(from_table=table)
    err = False
    try:
        contact.name = 'John Doe'
    except ValueError, e:
        err = True
    assert err


def test_create_table():
    table = Table()
    table.add_column(Column('email', 1, None, is_key=True))
    table.add_column(Column('firstname', 1))
    table.add_column(Column('lastname', 1))

    contact = Contact(from_table=table)
    contact.email = 'john@example.com'
    contact.firstname = 'John'
    contact.lastname = 'Doe'

    key_column = next(iter(table.key_columns), None)
    assert key_column == 'email'

    assert len(table.column_names) == 3


def test_engage_login_and_logout(engage_api):
    assert engage_api._session is None
    assert engage_api.login()
    assert isinstance(engage_api._session, Session)
    assert hasattr(engage_api._session, '_id')
    assert engage_api.logout()
    assert engage_api._session is None


def test_engage_basic_attributes(test_database):
    db = test_database

    str_keys = ('name', 'parent_name', 'user_id')
    for k in str_keys:
        assert hasattr(db, k)
        v = getattr(db, k)
        if v is not None:
            assert isinstance(v, basestring)

    int_keys = ('id', 'type', 'size', 'num_opt_outs', 'num_undeliverable', 'visibility', 'parent_folder_id',
                'suppression_list_id')
    for k in int_keys:
        assert hasattr(db, k)
        v = getattr(db, k)
        if v is not None:
            assert isinstance(v, int)

    date_keys = ('last_modified',)
    for k in date_keys:
        assert hasattr(db, k)
        v = getattr(db, k)
        if v is not None:
            assert isinstance(v, datetime.datetime)

    bool_keys = ('is_folder', 'flagged_for_backup')
    for k in bool_keys:
        assert hasattr(db, k)
        v = getattr(db, k)
        if v is not None:
            assert isinstance(v, bool)


def test_engage_get_meta_data(test_database):
    db = test_database

    # The database instance shouldn't have any meta props
    assert not hasattr(db, 'organization_id')
    assert not hasattr(db, 'created')
    assert not hasattr(db, 'last_configured')
    assert not hasattr(db, 'sms_keyword')

    # Fetch meta data
    assert db.get_meta_data()

    # We should have some meta information now
    assert hasattr(db, 'organization_id')
    assert hasattr(db, 'created')
    assert hasattr(db, 'last_configured')
    assert hasattr(db, 'sms_keyword')

    assert db.created == datetime.datetime(2012, 6, 13, 9, 9)
    assert db.sms_keyword is None

    assert db.opt_in_form_defined is True
    assert db.opt_out_form_defined is True
    assert db.profile_form_defined is True
    assert db.opt_in_autoreply_defined is True
    assert db.profile_autoreply_defined is True


def test_engage_get_databases(engage_api):
    dp = re.compile(r'^\<Database \'\d+\'\ \'[^\']+\'\>$')
    cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
    for database in engage_api.get_databases(LIST_VISIBILITY_SHARED):
        print database
        assert dp.match(repr(database)) is not None

        assert database.get_meta_data()

        for column in database._table._columns:
            assert cp.match(repr(column)) is not None
        #            print database


def test_engage_queries(engage_api):
    for query in engage_api.get_queries(LIST_VISIBILITY_SHARED):
        query.get_meta_data()
        print query


def test_get_contact_lists(engage_api):
    p = re.compile(r'^\<ContactList \'\d+\'\ \'[^\']+\'\>$')
    for contact_list in engage_api.get_contact_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(contact_list)) is not None
    #            print contact_list


def test_get_test_lists(engage_api):
    p = re.compile(r'^\<TestList \'\d+\'\ \'[^\']+\'\>$')
    for test_list in engage_api.get_test_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(test_list)) is not None
    #            print test_list


def test_get_suppression_lists(engage_api):
    p = re.compile(r'^\<SuppressionList \'\d+\'\ \'[^\']+\'\>$')
    for suppression_list in engage_api.get_suppression_lists(LIST_VISIBILITY_SHARED):
        assert p.match(repr(suppression_list)) is not None
    #            print suppression_list


def test_get_relational_tables(engage_api):
    cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
    for table in engage_api.get_relational_tables(LIST_VISIBILITY_SHARED):
        assert (table.get_meta_data())
        #            print table

        for column in table._columns:
            assert cp.match(repr(column)) is not None
