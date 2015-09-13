# -*- coding: utf-8 -*-

'''Sup-module tests
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

from freshmail.freshmail import FreshMail, FreshMailException


def test_init():
    fm_obj = FreshMail('key', 'secret')
    assert fm_obj.get_raw_response() == ''
    assert fm_obj.get_response() == ''
    assert fm_obj.get_errors() is None
    assert fm_obj.get_http_code() == 200

