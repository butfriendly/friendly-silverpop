# -*- coding: utf-8 -*-

"""
Original version borrowed from kennethreitz/python-github3. Thank you.

Copyright (c) 2011 Kenneth Reitz

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
"""

from datetime import datetime

from dateutil.parser import parse as parse_datetime

def to_python(obj,
    str_keys=None,
    date_keys=None,
    int_keys=None,
    object_map=None,
    bool_keys=None,
    dict_keys=None,
    **kwargs):
    """Extends a given object for API Consumption.

    :param obj: Object to extend.
    :param in_dict: Dict to extract data from.
    :param string_keys: List of in_dict keys that will be extracted as strings.
    :param date_keys: List of in_dict keys that will be extrad as datetimes.
    :param object_map: Dict of {key, obj} map, for nested object results.
    """

    if 'in_dict' in kwargs:
        def get_value(key):
            return kwargs.get('in_dict').get(key)
    elif 'in_el' in kwargs:
        def get_value(key):
            node = kwargs.get('in_el').find(key)
            if node is None:
                raise Exception('Node '+ key +' not found')
            return node.text
    else:
        raise Exception('Muhaa')

    d = dict()

    if str_keys:
        for in_key in str_keys:
            d[in_key.lower()] = get_value(in_key)

    if date_keys:
        for in_key in date_keys:
            in_date = get_value(in_key)
            try:
                out_date = parse_datetime(in_date)
            except TypeError, e:
                raise e
                out_date = None

            d[in_key.lower()] = out_date

    if int_keys:
        for in_key in int_keys:
            if get_value(in_key) is not None:
                d[in_key.lower()] = int(get_value(in_key))

    if bool_keys:
        for in_key in bool_keys:
            if get_value(in_key) is not None:
                d[in_key.lower()] = bool(get_value(in_key))

    if dict_keys:
        for in_key in dict_keys:
            if get_value(in_key) is not None:
                d[in_key.lower()] = dict(get_value(in_key))

    if object_map:
        for (k, v) in object_map.items():
            if get_value(k):
                d[k.lower()] = v.new_from_dict(get_value(k))

    obj.__dict__.update(d)
    obj.__dict__.update(kwargs)

    # Save the dictionary, for write comparisons.
    obj._cache = d
#    obj.__cache = in_dict

    return obj


def to_api(in_dict, int_keys=None, date_keys=None, bool_keys=None):
    """Extends a given object for API Production."""

    # Cast all int_keys to int()
    if int_keys:
        for in_key in int_keys:
            if (in_key in in_dict) and (in_dict.get(in_key, None) is not None):
                in_dict[in_key] = int(in_dict[in_key])

    # Cast all date_keys to datetime.isoformat
    if date_keys:
        for in_key in date_keys:
            if (in_key in in_dict) and (in_dict.get(in_key, None) is not None):

                _from = in_dict[in_key]

                if isinstance(_from, basestring):
                    dtime = parse_datetime(_from)

                elif isinstance(_from, datetime):
                    dtime = _from

                in_dict[in_key] = dtime.isoformat()

            elif (in_key in in_dict) and in_dict.get(in_key, None) is None:
                del in_dict[in_key]

    # Remove all Nones
    for k, v in in_dict.items():
        if v is None:
            del in_dict[k]

    return in_dict