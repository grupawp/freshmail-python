# -*- coding: utf-8 -*-

'''FreshMail (freshmail.pl) API module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

from copy import deepcopy
from hashlib import sha1

import requests
try:
    import simplejson as json
except ImportError:
    import json


HOST = 'https://api.freshmail.com'
PREFIX = '/rest/'

SUB_STATUS_ACTIVE = 1
SUB_STATUS_NOT_ACTIVATED = 3
SUB_STATUS = {
    SUB_STATUS_ACTIVE: 'active',
    2: 'activation pending',
    SUB_STATUS_NOT_ACTIVATED: 'not activated',
    4: 'resigned',
    5: 'soft bouncing',
    8: 'hard bouncing',
}

FIELD_TYPE_STR = 0
FIELD_TYPE_NUM = 1


class FreshMail(object):
    '''Freshmail REST API class
        Sends JSON requests to the FreshMail's API end-points
    '''

    def __init__(self, api_key, api_secret):
        '''Initiates communication object
        '''
        #: API's key (32 chars)
        self.api_key = api_key
        #: API's secret (40 chars)
        self.api_secret = api_secret
        #: last call API's raw response string (HTTP response body)
        self.raw_response = ''
        #: last call API's response (parsed JSON)
        self.response = ''
        #: last call errors table
        self.errors = None
        #: last call HTTP code
        self.http_code = 200
        #: request session object
        self.request_sess = requests.Session()


    def get_raw_response(self):
        '''Returns raw response data (string) from last call
        '''
        return self.raw_response


    def get_response(self):
        '''Returns parsed response data (JSON) from last call
        '''
        return self.response


    def get_errors(self):
        '''Returns all errors from last call
        '''
        return self.errors


    def get_http_code(self):
        '''Returns HTTP code from last call
        '''
        return self.http_code


    def request(self, url, payload=None, raw_response=False, method='POST'):
        '''Makes request to REST API. Adds payload data for POST request.
        :param url: API's controller[/action[/param1[/param2...]]]
        :param payload: POST data dict
        '''
        if payload is None:
            _data = ''
        else:
            _data = json.dumps(payload)

        access_path = PREFIX + url
        full_url = HOST + access_path
        sign_str = self.api_key + access_path + _data + self.api_secret
        api_sign = sha1(sign_str.encode('utf-8')).hexdigest()
        headers = {
            'Content-Type': 'application/json',
            'X-Rest-ApiKey': self.api_key,
            'X-Rest-ApiSign': api_sign,
        }
        if method == 'POST':
            res = self.request_sess.post(full_url, data=_data, headers=headers)
        elif method == 'GET':
            res = self.request_sess.get(full_url, data=_data, headers=headers)
        else:
            raise FreshMailException({
                'message': 'GET or POST required methods. Got {}'.format(
                    method)})

        self.http_code = res.status_code
        self.raw_response = res.content
        self.response = dict(res.json())

        self.errors = self.response.get('errors')
        if self.http_code != 200 and self.response.get('status') == 'ERROR':
            for error in self.errors:
                raise FreshMailException({
                    'message': error['message'],
                    'code': error['code'],
                })

        if raw_response:
            return self.raw_response
        return self.response


    def ping(self, payload=None, method='GET'):
        '''Pings service, returns ``"pong"`` for ``method="GET"`` or sends back
            payload for ``method="POST"``
        '''
        url = 'ping'
        return self.request(url, payload=payload, method=method)


    def subscriber_add(self, list_hash, subscriber_params, custom_fields=None):
        '''Adds a subscriber to the list
        '''
        payload = {
            'email': subscriber_params['email'],
            'list': list_hash,
            'state': subscriber_params.get('state', SUB_STATUS_NOT_ACTIVATED),
            'confirm': 1 if subscriber_params.get('confirm') else 0,
        }

        if custom_fields is not None:
            # custom_fields needs to be a dict
            if not isinstance(custom_fields, dict):
                raise FreshMailException({
                    'message': 'Custom fields must be a dict. Got {}'.format(
                        custom_fields)})
            payload['custom_fields'] = custom_fields

        url = 'subscriber/add'
        return self.request(url, payload)


    def subscribers_add(self, list_hash, subscribers_lst, state, confirm):
        '''Adds multiple subscribers to the list
        '''
        payload = {
            'list': list_hash,
            'subscribers': subscribers_lst,
            'state': state,
            'confirm': confirm,
        }

        url = 'subscriber/addMultiple'
        return self.request(url, payload)


    def subscriber_get(self, email, list_hash):
        '''Gets a subscriber from the list
        '''
        url = 'subscriber/get/' + '/'.join([list_hash, email])
        return self.request(url, method='GET')


    def subscriber_delete(self, email, list_hash):
        '''Removes a subscriber from the list
        '''
        payload = {
            'email': email,
            'list': list_hash,
        }

        url = 'subscriber/delete'
        return self.request(url, payload)


    def subscribers_list_fields(self, list_hash):
        '''Gets subscription list fields
        '''
        url = 'subscribers_list/getFields'
        return self.request(url, {'hash': list_hash})


    def subscribers_lists(self):
        '''Gets subscription lists
        '''
        url = 'subscribers_list/lists'
        response = dict(self.request(url, raw_response=False))
        if response.get('status') == 'OK':
            return response.get('lists')
        return None


    def subscriber_find_in_lists(self, email, lists):
        '''Finds subscriber at given lists
            NOTE: slow with large number of lists
        '''
        if not lists:
            raise FreshMailException({'message': 'No lists found'})
        subscribed_lists = []
        for one_list in lists:
            list_hash = one_list['subscriberListHash']
            try:
                result = self.subscriber_get(email, list_hash)
                subscribed_list = {
                    'list_hash': list_hash,
                    'name': one_list['name'],
                    'subscriber': result,
                }
                subscribed_lists.append(subscribed_list)
            except (FreshMailException, requests.exceptions.RequestException):
                pass

        return subscribed_lists


    def subscriber_find(self, email):
        '''Finds subscriber at available lists
            NOTE: slow with large number of lists
        '''
        lists = self.subscribers_lists()
        return self.subscriber_find_in_lists(email, lists)


    def subscribers_list_add_field(self, list_hash, field_name, tag=None,
                                   field_type=FIELD_TYPE_STR):
        '''Adds a custom field (text or numeric) to the list
        '''
        payload = {
            'hash': list_hash,
            'name': field_name,
            'type': field_type,
        }
        if tag is not None:
            payload['tag'] = tag

        url = 'subscribers_list/addField'
        return self.request(url, payload, method='POST')


    def transactional_mail(self, email, subject, extra_dc=None):
        '''Sends transactional email
        '''
        payload = {
            'subscriber': email,
            'subject': subject,
        }
        payload.update(extra_dc or {})

        url = 'mail'
        return self.request(url, payload)


    def mail_text(self, email, subject, text, extra_dc=None):
        '''Sends transactional plain text email
        '''
        extra_dc = deepcopy(extra_dc or {})
        extra_dc['text'] = text
        return self.transactional_mail(email, subject, extra_dc)


    def mail_html(self, email, subject, html, extra_dc=None):
        '''Sends transactional HTML email
        '''
        extra_dc = deepcopy(extra_dc or {})
        extra_dc['html'] = html
        return self.transactional_mail(email, subject, extra_dc)


class FreshMailException(Exception):
    '''Generic exception class for FreshMail REST API's operations
    '''
    pass
