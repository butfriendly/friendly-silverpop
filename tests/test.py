import nose
import re
from nose.tools import assert_equal, assert_is_not_none
from friendly.silverpop.engage import EngageApi, LIST_VISIBILITY_SHARED

class TestEngage(object):
    def setUp(self):
        self._api = EngageApi('username', 'password')

    def tearDown(self):
        pass

    def test_databases(self):
        dp = re.compile(r'^\<Database \'\d+\'\ \'[^\']+\'\>$')
        cp = re.compile(r'^\<Column \'[^\']+\'\ \'[^\']+\'\>$')
        for database in self._api.get_databases(LIST_VISIBILITY_SHARED):
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
