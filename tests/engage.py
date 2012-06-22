# -*- coding: utf-8 -*-

import nose
import re
import datetime
from nose.tools import assert_equal, assert_true, assert_false, assert_is_not_none
from friendly.silverpop.engage import EngageApi, LIST_VISIBILITY_SHARED
import settings

class TestDatabase(object):
    def setUp(self):
        self._api = EngageApi(settings.ENGAGE_USERNAME, settings.ENGAGE_PASSWORD, settings.ENGAGE_URL)

        # Fetch all shared databases of the account
        databases = self._api.get_databases(LIST_VISIBILITY_SHARED)

        # Locate our test database
        self._db = [db for db in databases if db.id == settings.ENGAGE_DATABASE_ID][0]

    def test_basic_attributes(self):
        db = self._db

        str_keys = ('name', 'parent_name', 'user_id')
        for k in str_keys:
            assert_true(hasattr(db, k))
            v = getattr(db, k)
            if v is not None:
                assert_true(isinstance(v, basestring))

        int_keys = ('id', 'type', 'size', 'num_opt_outs', 'num_undeliverable', 'visibility', 'parent_folder_id', 'suppression_list_id')
        for k in int_keys:
            assert_true(hasattr(db, k))
            v = getattr(db, k)
            if v is not None:
                assert_true(isinstance(v, int))

        date_keys = ('last_modified',)
        for k in date_keys:
            assert_true(hasattr(db, k))
            v = getattr(db, k)
            if v is not None:
                assert_true(isinstance(v, datetime.datetime))

        bool_keys = ('is_folder', 'flagged_for_backup')
        for k in bool_keys:
            assert_true(hasattr(db, k))
            v = getattr(db, k)
            if v is not None:
                assert_true(isinstance(v, bool))

    def test_get_meta_data(self):
        db = self._db

        # The database instance shouldn't have any meta props
        assert_false(hasattr(db, 'organization_id'))
        assert_false(hasattr(db, 'created'))
        assert_false(hasattr(db, 'last_configured'))
        assert_false(hasattr(db, 'sms_keyword'))

        # Fetch meta data
        assert_true(self._db.get_meta_data())

        # We should have some meta information now
        assert_true(hasattr(db, 'organization_id'))
        assert_true(hasattr(db, 'created'))
        assert_true(hasattr(db, 'last_configured'))
        assert_true(hasattr(db, 'sms_keyword'))

        assert_equal(db.created, datetime.datetime(2012, 6, 13, 9, 9))
        assert_equal(db.sms_keyword, None)

        assert_equal(db.opt_in_form_defined, True)
        assert_equal(db.opt_out_form_defined, True)
        assert_equal(db.profile_form_defined, True)
        assert_equal(db.opt_in_autoreply_defined, True)
        assert_equal(db.profile_autoreply_defined, True)

class TestEngage(object):
    def setUp(self):
        self._api = EngageApi(settings.ENGAGE_USERNAME, settings.ENGAGE_PASSWORD, settings.ENGAGE_URL)

    def tearDown(self):
        pass

    def test_databases(self):
        dp = re.compile(r'^\<Database \'\d+\'\ \'[^\']+\'\>$')
        cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
        for database in self._api.get_databases(LIST_VISIBILITY_SHARED):
            print database
            assert_is_not_none(dp.match(repr(database)))

            assert(database.get_meta_data())

            for column in database._columns:
                assert_is_not_none(cp.match(repr(column)))
#            print database

    def test_queries(self):
        for query in self._api.get_queries(LIST_VISIBILITY_SHARED):
            query.get_meta_data()
            print query

    def test_contact_lists(self):
        p = re.compile(r'^\<ContactList \'\d+\'\ \'[^\']+\'\>$')
        for contact_list in self._api.get_contact_lists(LIST_VISIBILITY_SHARED):
            assert_is_not_none(p.match(repr(contact_list)))
#            print contact_list

    def test_test_lists(self):
        p = re.compile(r'^\<TestList \'\d+\'\ \'[^\']+\'\>$')
        for test_list in self._api.get_test_lists(LIST_VISIBILITY_SHARED):
            assert_is_not_none(p.match(repr(test_list)))
#            print test_list

    def test_suppression_lists(self):
        p = re.compile(r'^\<SuppressionList \'\d+\'\ \'[^\']+\'\>$')
        for suppression_list in self._api.get_suppression_lists(LIST_VISIBILITY_SHARED):
            assert_is_not_none(p.match(repr(suppression_list)))
#            print suppression_list

    def test_tables(self):
        cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
        for table in self._api.get_relational_tables(LIST_VISIBILITY_SHARED):
            assert(table.get_meta_data())
#            print table

            for column in table._columns:
                assert_is_not_none(cp.match(repr(column)))
