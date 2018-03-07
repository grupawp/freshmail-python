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
    fm_obj = FreshMail('any_key', 'any_secret')
    assert fm_obj.get_raw_response() == ''
    assert fm_obj.get_response() == ''
    assert fm_obj.get_errors() is None
    assert fm_obj.get_http_code() == 200


def test_bad_method():
    fm_obj = FreshMail('any_key', 'any_secret')
    try:
        fm_obj.ping(method='PUT')
        assert False
    except FreshMailException:
        pass


def test_ping_no_auth():
    fm_obj = FreshMail('any_key', 'any_secret')
    try:
        res = fm_obj.ping()
        assert False
    except ValueError:
        pass


# vim: ts=4:sw=4:et:fdm=indent:ff=unix
