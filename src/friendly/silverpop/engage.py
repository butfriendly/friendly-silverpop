# -*- coding: utf-8 -*-

import sys
import collections
import requests
from xml.dom.minidom import Document
from xml.etree.ElementTree import ElementTree, fromstring
from helpers import to_python

LIST_VISIBILITY_PRIVATE = 0
LIST_VISIBILITY_SHARED  = 1

LIST_TYPE_DATABASE         = 0
LIST_TYPE_QUERY            = 1
LIST_TYPE_DATABASE_CONTACT_QUERY = 2
LIST_TYPE_TEST_LIST        = 5
LIST_TYPE_SEED_LIST        = 6
LIST_TYPE_SUPPRESSION_LIST = 13
LIST_TYPE_RELATIONAL_TABLE = 15
LIST_TYPE_CONTACT_LIST     = 18

COLUMN_TYPE_TEXT       = 0
COLUMN_TYPE_YESNO      = 1
COLUMN_TYPE_NUMERIC    = 2
COLUMN_TYPE_DATE       = 3
COLUMN_TYPE_TIME       = 4
COLUMN_TYPE_COUNTRY    = 5
COLUMN_TYPE_SELECTION  = 6
COLUMN_TYPE_SEGMENTING = 8
COLUMN_TYPE_SYSTEM     = 9
COLUMN_TYPE_SMS_OPT_OUT_DATE = 14
COLUMN_TYPE_SMS_PHONE_NUMBER = 15
COLUMN_TYPE_PHONE_NUMBER = 16
COLUMN_TYPE_TIMESTAMP    = 17
COLUMN_TYPE_MULTI_SELECT = 20

CONTACT_CREATED_FROM_DATABASE    = 0
CONTACT_CREATED_MANUALLY         = 1
CONTACT_CREATED_OPTED_IN         = 2
CONTACT_CREATED_FROM_TRACKING_DB = 3

class Resource(object):

    _string_keys = []
    _int_keys = []
    _date_keys = []
    _bool_keys = []
    _dict_keys = []
    _object_map = {}
#    _pks = []

    @classmethod
    def from_element(cls, el, api):
        return to_python(
            obj = cls(),
            in_el = el,
            str_keys = cls._str_keys,
            int_keys = cls._int_keys,
            date_keys = cls._date_keys,
            bool_keys = cls._bool_keys,
            dict_keys = cls._dict_keys,
            object_map = cls._object_map,
            _api = api
        )

class Session(object):
    def __init__(self, session_id):
        self._id = session_id

    def __str__(self):
        return self._id

    def close(self):
        pass

class Mailing(object):
    pass

class Contact(object):
    pass

class List(Resource):
    _str_keys = ['NAME', 'PARENT_NAME', 'USER_ID']
    _int_keys = ['ID', 'TYPE', 'SIZE', 'NUM_OPT_OUTS', 'NUM_UNDELIVERABLE', 'VISIBILITY', 'PARENT_FOLDER_ID', 'SUPPRESSION_LIST_ID']
    _date_keys = ['LAST_MODIFIED',]
    _bool_keys = ['IS_FOLDER','FLAGGED_FOR_BACKUP']
    _dict_keys = []
    _object_map = {}

    _contacts = {}

    @classmethod
    def from_element(cls, el, api):
        type = int(el.find('TYPE').text)

        if not type in LIST_TYPE_MAP:
            raise Exception("Unsupported type %d", type)

        list_class = LIST_TYPE_MAP[type]

        return super(cls, list_class).from_element(el, api)

    def add_contact(self, contact):
        if not isinstance(contact, Contact):
            raise ValueError('Invalid contact')

        self._api.add_recipient()
#        if not contact.id in self._contacts:
#            self._contacts[contact.id] = contact

#Column = collections.namedtuple('Column', ["title", "url", "dateadded", "format", "owner", "sizes", "votes"])
class MetaDataMixin(object):
    def get_meta_data(self):
        self._columns = []
        return self._api.get_list_meta_data(self)

class Column(object):
    def __init__(self, column_name, column_type=None, default_value=None):
        self._name = column_name
        self._type = column_type
        self._default = default_value

    def __repr__(self):
        return "<Column '{0}' '{1}'>".format(self._name, self._type)

class Database(List, MetaDataMixin):
    def __repr__(self):
        return "<Database '{0}' '{1}'>".format(self.id, self.name)

    def add_contact(self, contact):
#        self._api.add_recipient(self)
        raise NotImplementedError()

class Query(List, MetaDataMixin):
    def __repr__(self):
        return "<Query '{0}' '{1}'>".format(self.id, self.name)

class TestList(List):
    def __repr__(self):
        return "<TestList '{0}' '{1}'>".format(self.id, self.name)

class SeedList(List):
    def __repr__(self):
        return "<SeedList '{0}' '{1}'>".format(self.id, self.name)

class SuppressionList(List):
    def __repr__(self):
        return "<SuppressionList '{0}' '{1}'>".format(self.id, self.name)

class RelationalTable(List, MetaDataMixin):
    def __repr__(self):
        return "<RelationalTable '{0}' '{1}'>".format(self.id, self.name)

#    def import(self):
#        raise NotImplementedError()

    def export(self):
        raise NotImplementedError()

    def purge(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

class ContactList(List):
    def __repr__(self):
        return "<ContactList '{0}' '{1}'>".format(self.id, self.name)

LIST_TYPE_MAP = {
    LIST_TYPE_DATABASE : Database,
    LIST_TYPE_QUERY : Query,
    LIST_TYPE_TEST_LIST : TestList,
    LIST_TYPE_SEED_LIST : SeedList,
    LIST_TYPE_SUPPRESSION_LIST : SuppressionList,
    LIST_TYPE_RELATIONAL_TABLE : RelationalTable,
    LIST_TYPE_CONTACT_LIST : ContactList,
}

class EngageApi(object):
    def __init__(self, username, password, url, **kwargs):
        super(EngageApi, self).__init__()

        self._username = username
        self._password = password
        self._engage_url = url

        self._s = requests.session()

        self._session = None

    def _generate_envelope(self, action=None):
        """Generates common XML envelope for required for all requests"""
        doc = Document()

        # Create the <Envelope> base element
        envelope_node = doc.createElement('Envelope')
        doc.appendChild(envelope_node)

        # Create the <Body> base element
        body_node = doc.createElement('Body')
        envelope_node.appendChild(body_node)

        if action is not None:
            action_node = doc.createElement(action)
            body_node.appendChild(action_node)

            body_node = action_node

        return (body_node, doc)

    def _append_text_node_to(self, tag, text, target):
        """Creates a text node and appends it to the target"""
        doc = target.ownerDocument

        node = doc.createElement(tag)
        node.appendChild(doc.createTextNode(text))

        target.appendChild(node)

        return node

    def _check_session(self):
        if not self._session:
            self._login()
            if not self._session:
                raise Exception('No Session')

    def _login(self, username=None, password=None):
        if not username:
            username = self._username

        if not password:
            password = self._password

        body_node, doc = self._generate_envelope('Login')

        self._append_text_node_to('USERNAME', username, body_node)
        self._append_text_node_to('PASSWORD', password, body_node)

        response = self._request(doc, False)

        success, self.error = self._success(response)
        if success:
            tree = fromstring(response.text)
            p = tree.find("Body/RESULT/SESSIONID")
            self._session = Session(p.text)

        return success

    def _success(self, response):
        """Determines success state of a response"""
        tree = fromstring(response.text)
        p = tree.find("Body/RESULT/SUCCESS")
        success = p.text.upper() == 'TRUE'
        error = None
        if success == False:
            err_code = tree.find("Fault/Request/FaultCode")
            err_msg = tree.find("Fault/Request/FaultString")
            error = (err_code, err_msg)
            print response, error, response.text
        return (success, error)

    def _request(self, doc, session_required=True):
        if session_required:
            self._check_session()

        data = doc.toxml(encoding='utf-8')
        headers = {
            'Content-Type': 'text/xml;charset=UTF-8'
            }
        config = {
#            'verbose': sys.stderr
            }

        url = self._engage_url
        if session_required and self._session:
            url = '%s;jsessionid=%s' % (url, str(self._session))

        response = self._s.get(url, data=data, headers=headers, config=config)
        response.raise_for_status()

        return response

    def logout(self):
        raise NotImplementedError()

    def get_lists(self, visibility, list_type):
        body_node, doc = self._generate_envelope('GetLists')

        self._append_text_node_to('VISIBILITY', str(visibility), body_node)
        self._append_text_node_to('LIST_TYPE', str(list_type), body_node)

        response = self._request(doc)

        success, self.error = self._success(response)

        lists = []
        if success:
            tree = fromstring(response.text)
            for el in tree.findall("Body/RESULT/LIST"):
                list = List.from_element(el, self)
                lists.append(list)
        return lists

    def get_contact_lists(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_CONTACT_LIST)

    def get_databases(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_DATABASE)

    def get_queries(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_QUERY)

    def get_seed_lists(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_SEED_LIST)

    def get_test_lists(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_TEST_LIST)

    def get_suppression_lists(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_SUPPRESSION_LIST)

    def get_relational_tables(self, visibility):
        return self.get_lists(visibility, LIST_TYPE_RELATIONAL_TABLE)

    def get_recipient_mailings(self, list, recipient):
        if not isinstance(list, Database) and not isinstance(list, Query):
            raise Exception('Invalid list')

        if not isinstance(recipient, Contact):
            raise Exception('Invalid recipient')

        body_node, doc = self._generate_envelope('ListRecipientMailings')

        self._append_text_node_to('LIST_ID', str(list.id), body_node)
        self._append_text_node_to('RECIPIENT_ID', str(recipient.id), body_node)

        response = self._request(doc)

        success, self.error = self._success(response)

        print success, self.error

    def get_list_meta_data(self, list):
        if not isinstance(list, Database) and not isinstance(list, Query) and not isinstance(list, RelationalTable):
            raise Exception('Invalid list')

        body_node, doc = self._generate_envelope('GetListMetaData')

        self._append_text_node_to('LIST_ID', str(list.id), body_node)

        response = self._request(doc)

        success, self.error = self._success(response)

        if success:
            tree = fromstring(response.text)
            for item in tree.findall("Body/RESULT/COLUMNS/COLUMN"):
                column_name   = item.find('NAME').text
                column_type   = getattr(item.find('TYPE'), 'text', None)
                default_value = getattr(item.find('TYPE'), 'text', None)

                column = Column(column_name, column_type, default_value)
                list._columns.append(column)

        return success

    def remove_recipient(self, list, email=None, columns={}):
        if not isinstance(list, Database) and not isinstance(list, ContactList):
            raise Exception('Invalid list')

        if email is None and not columns:
            raise Exception('You need to define an email or columns')

        body_node, doc = self._generate_envelope('RemoveRecipient')

        self._append_text_node_to('LIST_ID', str(list.id), body_node)

        if email is not None:
            self._append_text_node_to('EMAIL', str(list.id), body_node)
        elif columns:
            for key in columns.keys():
                column_node = doc.createElement('COLUMN')
                body_node.appendChild(column_node)

                self._append_text_node_to('NAME', key, column_node)
                self._append_text_node_to('VALUE', columns[key], column_node)
        else:
            pass 

        response = self._request(doc)

        success, self.error = self._success(response)

        print success, self.error

    def create_table(self, name, columns):
        """Creates a Relational Table"""
        raise NotImplementedError()

    def join_table(self, **kwargs):
        if not 'table_name' in kwargs and not 'table_id' in kwargs:
            raise Exception('You need to define a table identifier')

        raise NotImplementedError()

    def insert_update_table(self, table_id, rows):
        raise NotImplementedError()

    def delete_table_data(self, table_id, rows):
        raise NotImplementedError()

    def import_table(self, map_file, source_file):
        raise NotImplementedError()

    def export_table(self, **kwargs):
        if not 'table_name' in kwargs and not 'table_id' in kwargs:
            raise Exception('You need to define a table identifier')

        raise NotImplementedError()

    def purge_table(self, **kwargs):
        if not 'table_name' in kwargs and not 'table_id' in kwargs:
            raise Exception('You need to define a table identifier')

        raise NotImplementedError()

    def delete_table(self, **kwargs):
        if not 'table_name' in kwargs and not 'table_id' in kwargs:
            raise Exception('You need to define a table identifier')

        raise NotImplementedError()

    def create_contact_list(self, database_id, list_name, visibility, **kwargs):
        raise NotImplementedError()

    def add_contact_to_contact_list(self, list_id, contact_id):
        raise NotImplementedError()

    def add_contact_to_program(self):
        raise NotImplementedError()

    def create_query(self):
        raise NotImplementedError()

    def calculate_query(self):
        raise NotImplementedError()

    def set_column_value(self, list_id, column_name, column_value):
        raise NotImplementedError()
    
    def purge_data(self, target_id, source_id):
        raise NotImplementedError()

    def add_recipient(self, database, created_from, **kwargs):
        if not isinstance(database, Database):
            raise ValueError('Invalid database')

        body_node, doc = self._generate_envelope('AddRecipient')

        self._append_text_node_to('CREATED_FROM', str(created_from), body_node)

        if 'send_autoreply' in kwargs:
            raise NotImplementedError()

        if 'update_if_found' in kwargs and kwargs.get('update_if_found') == True:
            self._append_text_node_to('UPDATE_IF_FOUND', 'true', body_node)

        if 'allow_html' in kwargs:
            raise NotImplementedError()

        if 'visitor_key' in kwargs:
            raise NotImplementedError()

        if 'sync_fields' in kwargs:
            raise NotImplementedError()

    def update_recipient(self, list_id, **kwargs):
        raise NotImplementedError()

    def double_opt_in_recipient(self):
        raise NotImplementedError()

    def opt_out_recipient(self):
        raise NotImplementedError()

    def select_recipient_data(self):
        raise NotImplementedError()
