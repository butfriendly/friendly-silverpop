import pytest
from friendly.silverpop.engage.resources import Table, Column, Contact
from friendly.silverpop.engage.constants import COLUMN_TYPE_TEXT, COLUMN_TYPE_YESNO


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

    assert len(table.column_names) == 3

    table.drop_column('firstname')

    assert len(table.column_names) == 2

    # We cannot delete key columns
    with pytest.raises(Exception) as e:
        table.drop_column('email')


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
    table.add_column(Column('email', COLUMN_TYPE_TEXT, None, is_key=True))
    table.add_column(Column('firstname', COLUMN_TYPE_TEXT))
    table.add_column(Column('lastname', COLUMN_TYPE_TEXT))
    table.add_column(Column('is_blue', COLUMN_TYPE_YESNO))

    contact = Contact(from_table=table)
    contact.email = 'john@example.com'
    contact.firstname = 'John'
    contact.lastname = 'Doe'
    contact.is_blue = True

    key_column = next(iter(table.key_columns), None)
    assert key_column == 'email'

    assert len(table.column_names) == 4