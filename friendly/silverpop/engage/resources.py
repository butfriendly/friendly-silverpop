from friendly.silverpop.helpers import to_python, pep_up
from .constants import (
    LIST_TYPE_DATABASE,
    LIST_TYPE_QUERY,
    LIST_TYPE_TEST_LIST,
    LIST_TYPE_SEED_LIST,
    LIST_TYPE_SUPPRESSION_LIST,
    LIST_TYPE_RELATIONAL_TABLE,
    LIST_TYPE_CONTACT_LIST,
    CONTACT_CREATED_MANUALLY)


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
