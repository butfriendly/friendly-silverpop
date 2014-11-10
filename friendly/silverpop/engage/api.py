import requests
from xml.dom.minidom import Document
from xml.etree.ElementTree import fromstring
from friendly.silverpop.helpers import to_python
from .constants import ERR_RECIPIENT_ALREADY_EXISTS, ERR_SESSION_EXPIRED_OR_INVALID, \
    LIST_TYPE_CONTACT_LIST, LIST_TYPE_DATABASE, LIST_TYPE_QUERY, LIST_TYPE_SEED_LIST, LIST_TYPE_TEST_LIST, \
    LIST_TYPE_SUPPRESSION_LIST, LIST_TYPE_RELATIONAL_TABLE, CONTACT_CREATED_FROM_DATABASE, CONTACT_CREATED_MANUALLY, \
    CONTACT_CREATED_FROM_TRACKING_DB, CONTACT_CREATED_OPTED_IN, EXPORT_TYPE_ALL, EXPORT_TYPE_OPT_IN, EXPORT_TYPE_OPT_OUT, \
    EXPORT_TYPE_UNDELIVERABLE, EXPORT_FORMAT_CSV, EXPORT_FORMAT_TAB, EXPORT_FORMAT_PIPE
from .exceptions import (
    RecipientAlreadyExistsError, SessionIsExpiredOrInvalidError, EngageError, UnsupportedExportTypeError,
    UnsupportedExportFormatError)
from .resources import (
    Session, List, Column, Table, Contact, Database, Query, RelationalTable)


CONTACT_CREATED_CHOICES = (
    CONTACT_CREATED_FROM_DATABASE,
    CONTACT_CREATED_MANUALLY,
    CONTACT_CREATED_OPTED_IN,
    CONTACT_CREATED_FROM_TRACKING_DB,
)

EXPORT_TYPE_CHOICES = (
    EXPORT_TYPE_ALL,
    EXPORT_TYPE_OPT_IN,
    EXPORT_TYPE_OPT_OUT,
    EXPORT_TYPE_UNDELIVERABLE,
)

EXPORT_FORMAT_CHOICES = (
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_TAB,
    EXPORT_FORMAT_PIPE,
)


def generate_envelope(action=None):
    """Generates common XML envelope which is required for all requests."""
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


def append_text_node_to(tag, text, target):
    """Creates a text node and appends it to the target"""
    doc = target.ownerDocument

    node = doc.createElement(tag)
    node.appendChild(doc.createTextNode(text))

    target.appendChild(node)

    return node


def append_columns_to(columns, target):
    return append_namevalue_nodes_to(columns, target)


def append_sync_fields_to(fields, target):
    return append_namevalue_nodes_to(
        fields, target, container_node_name='SYNC_FIELDS',
        item_node_name='SYNC_FIELD')


def append_namevalue_nodes_to(nv, target, **kwargs):
    assert isinstance(nv, dict)
    container_node_name = kwargs.get('container_node_name')
    item_node_name = kwargs.get('item_node_name', 'COLUMN')

    doc = target.ownerDocument

    container_node = None
    if container_node_name:
        container_node = doc.createElement(container_node_name)

    for name in nv.keys():
        item_node = doc.createElement(item_node_name)
        append_text_node_to('NAME', name, item_node)
        append_text_node_to('VALUE', nv[name], item_node)
        if container_node:
            container_node.appendChild(item_node)
        else:
            target.appendChild(item_node)

    if container_node:
        target.appendChild(container_node)


def append_list_to(items, target, **kwargs):
    assert isinstance(items, list)
    container_node_name = kwargs.get('container_node_name', 'COLUMNS')
    item_node_name = kwargs.get('item_node_name', 'COLUMN')

    doc = target.ownerDocument

    container_node = None
    if container_node_name:
        container_node = doc.createElement(container_node_name)

    for item in items:
        append_text_node_to(item_node_name, item, container_node)

    target.appendChild(container_node)


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

    def has_errors(self, response, raise_on_error=True):
        """Determines the state of a request"""
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
        """Acquires a silverpop session"""
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

        body_node, doc = generate_envelope('Login')
        append_text_node_to('USERNAME', username, body_node)
        append_text_node_to('PASSWORD', password, body_node)

        (success, tree, self.error) = self.get(doc, False)
        if success:
            session_id = tree.find("Body/RESULT/SESSIONID").text
            self._session = Session(session_id)

        return success

    def logout(self):
        """Logs out from Engage's API and removes the session"""
        body_node, doc = generate_envelope('Logout')
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
        body_node, doc = generate_envelope('GetLists')
        append_text_node_to('VISIBILITY', str(visibility), body_node)
        append_text_node_to('LIST_TYPE', str(list_type), body_node)

        (success, tree, self.error) = self.get(doc)

        lists = []
        if success:
            for el in tree.findall('Body/RESULT/LIST'):
                list = List.from_element(el, self)
                lists.append(list)
        return lists

    def export_list(self, database, export_type, export_format, **kwargs):
        list_id = database
        if isinstance(database, Database):
            list_id = database.id

        if 'email' in kwargs:
            raise NotImplementedError()

        if 'add_to_stored_files' in kwargs:
            raise NotImplementedError()

        if 'date_start' in kwargs:
            raise NotImplementedError()

        if 'date_end' in kwargs:
            raise NotImplementedError()

        if 'use_created_date' in kwargs:
            raise NotImplementedError()

        if 'include_lead_source' in kwargs:
            raise NotImplementedError()

        if 'list_date_format' in kwargs:
            raise NotImplementedError()

        if 'export_columns' in kwargs:
            raise NotImplementedError()

        if not export_type in EXPORT_TYPE_CHOICES:
            raise UnsupportedExportTypeError('%s is not supported' % export_type)

        if not export_format in EXPORT_FORMAT_CHOICES:
            raise UnsupportedExportFormatError('%s is not supported' % export_format)

        file_encoding = kwargs.get('file_encoding', 'utf-8')

        body_node, doc = generate_envelope('ExportList')
        append_text_node_to('LIST_ID', str(list_id), body_node)
        append_text_node_to('EXPORT_TYPE', export_type, body_node)
        append_text_node_to('EXPORT_FORMAT', export_format, body_node)
        append_text_node_to('FILE_ENCODING', file_encoding, body_node)

        (success, tree, self.error) = self.get(doc)

        job_id = tree.find('Body/RESULT/JOB_ID').text
        file_path = tree.find('Body/RESULT/FILE_PATH').text

        return (success, job_id, file_path)

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

        body_node, doc = generate_envelope('ListRecipientMailings')
        append_text_node_to('LIST_ID', str(list.id), body_node)
        append_text_node_to('RECIPIENT_ID', str(recipient.id), body_node)

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

        body_node, doc = generate_envelope('GetListMetaData')

        append_text_node_to('LIST_ID', str(list.id), body_node)

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

        body_node, doc = generate_envelope('RemoveRecipient')
        append_text_node_to('LIST_ID', str(list_id), body_node)

        if email is not None:
            append_text_node_to('EMAIL', email, body_node)
        elif columns:
            append_columns_to(columns, body_node)
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

    def create_contact_list(self, list_id, list_name, visibility, **kwargs):
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

        body_node, doc = generate_envelope('AddRecipient')
        append_text_node_to('LIST_ID', str(list_id), body_node)
        append_text_node_to('CREATED_FROM', str(created_from), body_node)

        if 'update_if_found' in kwargs and kwargs.get('update_if_found') is True:
            append_text_node_to('UPDATE_IF_FOUND', 'true', body_node)

        contact_lists = kwargs.get('contact_lists', [])
        assert not isinstance(contact_lists, basestring)
        if contact_lists:
            contact_lists_node = doc.createElement('CONTACT_LISTS')
            for contact_id in contact_lists:
                append_text_node_to('CONTACT_LIST_ID', contact_id, contact_lists_node)
            body_node.appendChild(contact_lists_node)

        assert isinstance(columns, dict)
        append_columns_to(columns, body_node)

        sync_fields = kwargs.get('sync_fields', {})
        assert isinstance(sync_fields, dict)
        append_sync_fields_to(sync_fields, body_node)

        (success, tree, self.error) = self.get(doc)

        return success

    def update_recipient(self, list_id, columns, **kwargs):
        """Updates a contact"""
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

        body_node, doc = generate_envelope('UpdateRecipient')
        append_text_node_to('LIST_ID', str(list_id), body_node)

        old_email = kwargs.get('old_email')
        if old_email:
            append_text_node_to('OLD_EMAIL', old_email, body_node)

        # Append columns
        assert isinstance(columns, dict)
        append_columns_to(columns, body_node)

        # Append sync fields
        sync_fields = kwargs.get('sync_fields', {})
        assert isinstance(sync_fields, dict)
        append_sync_fields_to(sync_fields, body_node)

        (success, tree, self.error) = self.get(doc)

        return success

    def double_opt_in_recipient(self):
        raise NotImplementedError()

    def opt_out_recipient(self):
        raise NotImplementedError()

    def select_recipient_data(self, list_id, email, **kwargs):
        """Queries a contact's details"""
        body_node, doc = generate_envelope('SelectRecipientData')
        append_text_node_to('LIST_ID', str(list_id), body_node)
        append_text_node_to('EMAIL', str(email), body_node)

        recipient_id = kwargs.get('recipient_id')
        if recipient_id:
            append_text_node_to('RECIPIENT_ID', str(recipient_id), body_node)

        encoded_recipient_id = kwargs.get('encoded_recipient_id')
        if recipient_id:
            append_text_node_to('ENCODED_RECIPIENT_ID', str(encoded_recipient_id), body_node)

        visitor_key = kwargs.get('visitor_key')
        if recipient_id:
            append_text_node_to('VISITOR_KEY', str(visitor_key), body_node)

        (success, tree, self.error) = self.get(doc)
        if success:
            for el in tree.findall('Body/RESULT'):
                return Contact.from_element(el, self)
