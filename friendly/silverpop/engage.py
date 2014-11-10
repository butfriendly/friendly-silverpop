# -*- coding: utf-8 -*-

import sys
import collections
import requests
from xml.dom.minidom import Document
from xml.etree.ElementTree import ElementTree, fromstring
from helpers import to_python, pep_up

LIST_VISIBILITY_PRIVATE = 0
LIST_VISIBILITY_SHARED = 1

LIST_TYPE_DATABASE = 0
LIST_TYPE_QUERY = 1
LIST_TYPE_DATABASE_CONTACT_QUERY = 2
LIST_TYPE_TEST_LIST = 5
LIST_TYPE_SEED_LIST = 6
LIST_TYPE_SUPPRESSION_LIST = 13
LIST_TYPE_RELATIONAL_TABLE = 15
LIST_TYPE_CONTACT_LIST = 18

COLUMN_TYPE_TEXT = 0
COLUMN_TYPE_YESNO = 1
COLUMN_TYPE_NUMERIC = 2
COLUMN_TYPE_DATE = 3
COLUMN_TYPE_TIME = 4
COLUMN_TYPE_COUNTRY = 5
COLUMN_TYPE_SELECTION = 6
COLUMN_TYPE_SEGMENTING = 8
COLUMN_TYPE_SYSTEM = 9
COLUMN_TYPE_SMS_OPT_OUT_DATE = 14
COLUMN_TYPE_SMS_PHONE_NUMBER = 15
COLUMN_TYPE_PHONE_NUMBER = 16
COLUMN_TYPE_TIMESTAMP = 17
COLUMN_TYPE_MULTI_SELECT = 20

CONTACT_CREATED_FROM_DATABASE = 0
CONTACT_CREATED_MANUALLY = 1
CONTACT_CREATED_OPTED_IN = 2
CONTACT_CREATED_FROM_TRACKING_DB = 3

CONTACT_CREATED_CHOICES = (
    CONTACT_CREATED_FROM_DATABASE,
    CONTACT_CREATED_MANUALLY,
    CONTACT_CREATED_OPTED_IN,
    CONTACT_CREATED_FROM_TRACKING_DB,
)

ERR_RECIPIENT_ALREADY_EXISTS = 122
ERR_RECIPIENT_IS_NOT_A_MEMBER = 128
ERR_SESSION_EXPIRED_OR_INVALID = 145

#ENGAGE_ERRORS = (
#    (ERR_RECIPIENT_IS_NOT_A_MEMBER, EngageError),
#    (ERR_SESSION_EXPIRED_OR_INVALID, EngageError),
#)


class Resource(object):
    _str_keys = []
    _int_keys = []
    _date_keys = []
    _bool_keys = []
    _dict_keys = []
    _object_map = {}
    # _pks = []

    @classmethod
    def from_element(cls, el, api):
        return to_python(
            obj=cls(),
            in_el=el,
            str_keys=cls._str_keys,
            int_keys=cls._int_keys,
            date_keys=cls._date_keys,
            bool_keys=cls._bool_keys,
            dict_keys=cls._dict_keys,
            object_map=cls._object_map,
            api=api
        )


class Session(object):
    def __init__(self, session_id):
        self.id = session_id

    def __str__(self):
        return self.id

    def close(self):
        pass


class Mailing(object):
    pass


class Contact(Resource):
    _str_keys = ('EMAIL', 'ORGANIZATION_ID')
    _int_keys = ('RecipientId', 'EmailType', 'CreatedFrom')
    _date_keys = ('LastModified', )
    _bool_keys = []
    _dict_keys = None
    _object_map = {}

    def __init__(self, **kwargs):
        table = kwargs.get('from_table')

#        if table is None:
#            table = Table()

        self.__dict__['_table'] = table

    def __setattr__(self, name, value):
        if self._table and not self._table.has_column(name):
            raise ValueError(
                'Contact has no field "{0}". Available fields: {1}'.format(name, ', '.join(self._table.column_names)))

        # @todo Validate type

        super(Contact, self).__setattr__(name, value)


class List(Resource):
    _str_keys = ('NAME', 'PARENT_NAME', 'USER_ID')
    _int_keys = ('ID', 'TYPE', 'SIZE', 'NUM_OPT_OUTS', 'NUM_UNDELIVERABLE', 'VISIBILITY',
                 'PARENT_FOLDER_ID', 'SUPPRESSION_LIST_ID')
    _date_keys = ('LAST_MODIFIED',)
    _bool_keys = ('IS_FOLDER', 'FLAGGED_FOR_BACKUP')
    _dict_keys = None
    _object_map = {}

    # def __init__(self):
    #        self._contacts = {}

    @classmethod
    def from_element(cls, el, api):
        type = int(el.find('TYPE').text)

        if not type in LIST_TYPE_MAP:
            raise Exception("Unsupported type %d", type)

        list_class = LIST_TYPE_MAP[type]

        return super(cls, list_class).from_element(el, api)

    def add_contact(self, contact, created_from=CONTACT_CREATED_MANUALLY):
        if not isinstance(contact, Contact):
            raise ValueError('Invalid contact')

        return self.api.add_recipient(self.id, created_from, contact)

    def get_recipient_data(self, contact):
        if not isinstance(contact, Contact):
            raise ValueError('Invalid contact')

        return self.api.select_recipient_data(self.id, contact.email)


# if not contact.id in self._contacts:
#            self._contacts[contact.id] = contact

#Column = collections.namedtuple('Column', ["title", "url", "dateadded", "format", "owner", "sizes", "votes"])
class MetaDataMixin(object):
    def get_meta_data(self):
        return self.api.get_list_meta_data(self)


class Column(object):
    def __init__(self, column_name, column_type=None, default_value=None, **kwargs):
        self._mapping = {}  # Map for remembering old and ugly column names

        self.id = pep_up(column_name)  # Clean up the name
        self._mapping[self.id] = column_name  # Remember the name

        self.name = column_name
        self.type = column_type
        self.default = default_value

        self.is_key = kwargs.get('is_key', False)

    def __str__(self):
        return self.id

    def __repr__(self):
        return "<Column name={0} type={1}>".format(self.name, self.type)


class Table(object):
    def __init__(self):
        self._columns = {}

    @property
    def key_columns(self):
        """Returns a list of key columns of the table"""
        return [str(column) for id, column in self._columns.iteritems() if column.is_key]

    @property
    def column_names(self):
        return [str(column) for id, column in self._columns.iteritems()]

    def has_column(self, column_name):
        """Checks wether the table contains the given column

        Args:
            column_name (str): Name of the column to check for

        Returns:
            bool -- Wether the column exists or not
        """
        return column_name in self._columns

    def add_column(self, column, replace=False, **kwargs):
        """Adds/replaces a column at the table

        Args:
            column (Column): Column to add
            replace (bool): Wether to replace existing columns with the same id or not

        Raises:
            ValueError
        """
        if not isinstance(column, Column):
            raise ValueError('Invalid value. Must be column')

        if not hasattr(column, 'id'):
            raise Exception('No id at column')

        # We return silently if the column already exists
        if str(column) in self._columns and replace is False:
            # raise Exception('Column "{0}" already exists'.format(str(column)))
            return

        self._columns[str(column)] = column

    def drop_column(self, column):
        column_name = None

        if isinstance(column, Column):
            column_name = column.name
        elif isinstance(column, basestring):
            column_name = column
        else:
            raise ValueError('Invalid column type')

        if not column_name in self.column_names:
            raise Exception('No column %s' % column_name)

        if self._columns[column_name].is_key:
            raise Exception('Cannot delete key columns')

        del self._columns[column_name]


class Database(List, MetaDataMixin):
    def __repr__(self):
        return "<Database '{0}' '{1}'>".format(self.id, self.name)

    def create_contact(self):
        """Creates a new contact.

        Returns:
            Contact -- A new instance of a Contact. 

            NOTE: The instance acts only as a DTO and won't be persistet 
                  until calling ``add_contact``.
        """
        if not hasattr(self, '_table'):
            self.get_meta_data()

        return Contact(from_table=self._table)


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
    LIST_TYPE_DATABASE: Database,
    LIST_TYPE_QUERY: Query,
    LIST_TYPE_TEST_LIST: TestList,
    LIST_TYPE_SEED_LIST: SeedList,
    LIST_TYPE_SUPPRESSION_LIST: SuppressionList,
    LIST_TYPE_RELATIONAL_TABLE: RelationalTable,
    LIST_TYPE_CONTACT_LIST: ContactList,
}


class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg, code=None):
        self.msg = msg
        self.code = code

    def __str__(self):
        return '%s (%r)' % (self.msg, self.code)


class EngageError(Error):
    pass


class SessionIsExpiredOrInvalidError(EngageError):
    pass


class RecipientAlreadyExistsError(EngageError):
    pass


class EngageApiCore(object):
    def __init__(self):
        self._username = None
        self._password = None
        self._engage_url = None

        self._session = None  # SilverPop session

        self._requests = requests.session()  # Requests session

    @property
    def session(self):
        return self._session

    def generate_envelope(self, action=None):
        """Generates common XML envelope which is required for all requests"""
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

    def append_text_node_to(self, tag, text, target):
        """Creates a text node and appends it to the target"""
        doc = target.ownerDocument

        node = doc.createElement(tag)
        node.appendChild(doc.createTextNode(text))

        target.appendChild(node)

        return node

    def append_columns_to(self, columns, target):
        return self._append_namevalue_nodes_to(columns, target)

    def append_sync_fields_to(self, fields, target):
        return self._append_namevalue_nodes_to(
            fields, target, container_node_name='SYNC_FIELDS',
            item_node_name='SYNC_FIELD')

    def _append_namevalue_nodes_to(self, nv, target, **kwargs):
        assert isinstance(nv, dict)
        container_node_name = kwargs.get('container_node_name')
        item_node_name = kwargs.get('item_node_name', 'COLUMN')

        doc = target.ownerDocument

        container_node = None
        if container_node_name:
            container_node = doc.createElement(container_node_name)

        for name in nv.keys():
            item_node = doc.createElement(item_node_name)
            self.append_text_node_to('NAME', name, item_node)
            self.append_text_node_to('VALUE', nv[name], item_node)
            if container_node:
                container_node.appendChild(item_node)
            else:
                target.appendChild(item_node)

        if container_node:
            target.appendChild(container_node)

    def has_errors(self, response, raise_on_error=True):
        """Determines success state of a response"""
        tree = fromstring(response.text)
        success = tree.find('Body/RESULT/SUCCESS').text
        was_successful = success.upper() == 'TRUE'

        error = None
        if not was_successful:
            # Extract error code and message
            err_code = tree.find('Body/Fault/FaultCode').text
            err_msg = tree.find('Body/Fault/FaultString').text
            err_id = int(tree.find('Body/Fault/detail/error/errorid').text)
            if raise_on_error:
                # @todo Improve exceptions
                if err_id == ERR_RECIPIENT_ALREADY_EXISTS:
                    raise RecipientAlreadyExistsError(err_msg, err_code)
                elif err_id == ERR_SESSION_EXPIRED_OR_INVALID:
                    raise SessionIsExpiredOrInvalidError('%s: %s' % (err_msg, self.session.id))
                else:
                    raise EngageError(err_msg, err_code)
            error = (err_code, err_msg)

        return (was_successful, tree, error)

    def acquire_session(self):
        if not self.session:
            self.login()
            if not self.session:
                raise EngageError('No Session')

    def _request(self, doc, session_required=True):
        """Wraps the whole request mechanism"""
        if session_required:
            self.acquire_session()

        data = doc.toxml(encoding='utf-8')
        headers = {
            'Content-Type': 'text/xml;charset=UTF-8',
        }

        url = self._engage_url

        # Append jsessionid to URL if we have a session
        if self._session is not None:
            url += ';jsessionid=%s' % str(self._session)

        response = self._requests.get(url, data=data, headers=headers)
        response.raise_for_status()

        return response

    def get(self, doc, session_required=True, raise_on_error=True):
        response = self._request(doc, session_required)
        return self.has_errors(response, raise_on_error)

    def login(self, username=None, password=None):
        """Logs in to Engage's API.

        Args:
            username (str): Username to use when logging in. Overrides username given at instantiaton.
            password (str): Password to use when logging in. Overrides password given at instantiaton.

        Returns:
            bool -- Wether the login was successful for not
        """
        if not username:
            username = self._username

        if not password:
            password = self._password

        body_node, doc = self.generate_envelope('Login')
        self.append_text_node_to('USERNAME', username, body_node)
        self.append_text_node_to('PASSWORD', password, body_node)

        (success, tree, self.error) = self.get(doc, False)
        if success:
            session_id = tree.find("Body/RESULT/SESSIONID").text
            self._session = Session(session_id)

        return success

    def logout(self):
        """Logs out from Engage's API and removes the session"""
        body_node, doc = self.generate_envelope('Logout')
        (success, tree, self.error) = self.get(doc)
        if success:
            self._session = None

        return success


class EngageApi(EngageApiCore):
    def __init__(self, username, password, url, **kwargs):
        super(EngageApi, self).__init__()

        self._username = username
        self._password = password
        self._engage_url = url

    def get_lists(self, visibility, list_type):
        """Fetches lists.

        Args:
            visibility (int): Visibility of the lists you want to fetch.
            list_type (int): Type of lists you want to fetch

        Returns:
            list -- List of lists. Whereby the type depends on the list_type you requested.
        """
        body_node, doc = self.generate_envelope('GetLists')

        self.append_text_node_to('VISIBILITY', str(visibility), body_node)
        self.append_text_node_to('LIST_TYPE', str(list_type), body_node)

        (success, tree, self.error) = self.get(doc)

        lists = []
        if success:
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

        body_node, doc = self.generate_envelope('ListRecipientMailings')

        self.append_text_node_to('LIST_ID', str(list.id), body_node)
        self.append_text_node_to('RECIPIENT_ID', str(recipient.id), body_node)

        (success, tree, self.error) = self.get(doc)

        print success, self.error

    def get_list_meta_data(self, list):
        """Fetches meta-data and updates the list with 'em.

        Args:
            list (List): List you want to fetch the meta-data for.

        Returns:
            bool -- Tells you wether the operation was successful or not

        .. note::
            ``KEY_COLUMNS`` and ``SELECTION_VALUES`` aren't supported currently.
        """
        if not isinstance(list, Database) and not isinstance(list, Query) and not isinstance(list, RelationalTable):
            raise Exception('Invalid list')

        body_node, doc = self.generate_envelope('GetListMetaData')

        self.append_text_node_to('LIST_ID', str(list.id), body_node)

        (success, tree, self.error) = self.get(doc)
        if success:
            result_node = tree.find('Body/RESULT')

            table = Table()

            for item in result_node.findall('KEY_COLUMNS/COLUMN'):
                # @todo: DRY
                column_name = item.find('NAME').text
                column_type = getattr(item.find('TYPE'), 'text', None)
                default_value = getattr(item.find('DEFAULT_VALUE'), 'text', None)

                table.add_column(Column(column_name, column_type, default_value, is_key=True))

            # NOTE: ``COLUMNS`` contains also ``KEY_COLUMNS``
            for item in result_node.findall('COLUMNS/COLUMN'):
                # @todo: DRY
                column_name = item.find('NAME').text
                column_type = getattr(item.find('TYPE'), 'text', None)
                default_value = getattr(item.find('DEFAULT_VALUE'), 'text', None)

                # @todo Add support for selection values
                #                for selection_value in item.find('SELECTION_VALUES/VALUE'):
                #                    pass

                table.add_column(Column(column_name, column_type, default_value))

            to_python(list,
                      in_el=result_node,
                      str_keys=('ORGANIZATION_ID', ),
                      date_keys=('LAST_CONFIGURED', 'CREATED'),
                      bool_keys=('OPT_IN_FORM_DEFINED', 'OPT_OUT_FORM_DEFINED', 'PROFILE_FORM_DEFINED',
                                 'OPT_IN_AUTOREPLY_DEFINED', 'PROFILE_AUTOREPLY_DEFINED'),
                      _table=table)

        return success

    def remove_recipient(self, list_id, email=None, columns={}):
        if email is None and not columns:
            raise Exception('You need to define an email or columns')

        body_node, doc = self.generate_envelope('RemoveRecipient')

        self.append_text_node_to('LIST_ID', str(list_id), body_node)

        if email is not None:
            self.append_text_node_to('EMAIL', email, body_node)
        elif columns:
            self.append_columns_to(columns, body_node)
        else:
            pass

        (success, tree, self.error) = self.get(doc)

        return success

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

    def add_recipient(self, list_id, created_from, columns, **kwargs):
        """Adds a new contact to an existing database"""
        if not created_from in CONTACT_CREATED_CHOICES:
            raise EngageError('Invalid CREATED_FROM')

        if 'send_autoreply' in kwargs:
            raise NotImplementedError()

        if 'allow_html' in kwargs:
            raise NotImplementedError()

        if 'visitor_key' in kwargs:
            raise NotImplementedError()

        body_node, doc = self.generate_envelope('AddRecipient')

        self.append_text_node_to('LIST_ID', str(list_id), body_node)
        self.append_text_node_to('CREATED_FROM', str(created_from), body_node)

        if 'update_if_found' in kwargs and kwargs.get('update_if_found') is True:
            self.append_text_node_to('UPDATE_IF_FOUND', 'true', body_node)

        contact_lists = kwargs.get('contact_lists', [])
        assert not isinstance(contact_lists, basestring)
        if contact_lists:
            contact_lists_node = doc.createElement('CONTACT_LISTS')
            for contact_id in contact_lists:
                self.append_text_node_to('CONTACT_LIST_ID', contact_id, contact_lists_node)
            body_node.appendChild(contact_lists_node)

        assert isinstance(columns, dict)
        self.append_columns_to(columns, body_node)

        sync_fields = kwargs.get('sync_fields', {})
        assert isinstance(sync_fields, dict)
        self.append_sync_fields_to(sync_fields, body_node)

        (success, tree, self.error) = self.get(doc)

        return success

    def update_recipient(self, list_id, columns, **kwargs):
        if 'recipient_id' in kwargs:
            raise NotImplementedError()

        if 'encoded_recipient_id' in kwargs:
            raise NotImplementedError()

        if 'send_autoreply' in kwargs:
            raise NotImplementedError()

        if 'allow_html' in kwargs:
            raise NotImplementedError()

        if 'visitor_key' in kwargs:
            raise NotImplementedError()

        if 'sync_fields' in kwargs:
            raise NotImplementedError()

        if 'snooze_settings' in kwargs:
            raise NotImplementedError()

        body_node, doc = self.generate_envelope('UpdateRecipient')

        old_email = kwargs.get('old_email')
        if old_email:
            self.append_text_node_to('OLD_EMAIL', old_email, body_node)

        self.append_text_node_to('LIST_ID', str(list_id), body_node)

        assert isinstance(columns, dict)
        self.append_columns_to(columns, body_node)

        sync_fields = kwargs.get('sync_fields', {})
        assert isinstance(sync_fields, dict)
        self.append_sync_fields_to(sync_fields, body_node)

        (success, tree, self.error) = self.get(doc)

        return success

    def double_opt_in_recipient(self):
        raise NotImplementedError()

    def opt_out_recipient(self):
        raise NotImplementedError()

    def select_recipient_data(self, list_id, email, **kwargs):
        """

        :param list_id:
        :type list_id:
        :param email:
        :type email:
        :param kwargs:
        :type kwargs:
        :rtype: Contact
        """
        body_node, doc = self.generate_envelope('SelectRecipientData')
        self.append_text_node_to('LIST_ID', str(list_id), body_node)
        self.append_text_node_to('EMAIL', str(email), body_node)

        recipient_id = kwargs.get('recipient_id')
        if recipient_id:
            self.append_text_node_to('RECIPIENT_ID', str(recipient_id), body_node)

        encoded_recipient_id = kwargs.get('encoded_recipient_id')
        if recipient_id:
            self.append_text_node_to('ENCODED_RECIPIENT_ID', str(encoded_recipient_id), body_node)

        visitor_key = kwargs.get('visitor_key')
        if recipient_id:
            self.append_text_node_to('VISITOR_KEY', str(visitor_key), body_node)

        (success, tree, self.error) = self.get(doc)
        if success:
            for el in tree.findall("Body/RESULT"):
                return Contact.from_element(el, self)
