# -*- coding: utf-8 -*-

import nose
import re
import datetime
from friendly.silverpop.engage.resources import Database


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
    db = Database()
    db.id = test_database.id
    db.api = test_database.api

    # The database instance shouldn't have any meta props
    assert not hasattr(db, 'organization_id')
    assert not hasattr(db, 'created')
    assert not hasattr(db, 'last_configured')

    # Fetch meta data
    assert db.get_meta_data()

    # We should have some meta information now
    assert hasattr(db, 'organization_id')
    assert hasattr(db, 'created')
    assert hasattr(db, 'last_configured')

    assert isinstance(db.created, datetime.datetime)

    assert db.opt_in_form_defined is True
    assert db.opt_out_form_defined is True
    assert db.profile_form_defined is True
    assert db.opt_in_autoreply_defined is True
    assert db.profile_autoreply_defined is True
