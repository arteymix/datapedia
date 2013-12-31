# -*- Mode: Python; coding: utf-8; indent-tabs-mode: s; c-basic-offset: 4; tab-width: 4 -*- 
#
# Copyright (C) 2013 Guillaume Poirier-Morency <guillaume@guillaume-fedora-netbook>
# 
# Datapedia is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Datapedia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps
import json
import md5

def detectresponse(f):
    """Detect response type to apply by looking at the ext attribute"""
    @wraps(f)
    def wrapper(**args):
        if 'ext' in args:
            ext = args['ext']

            if ext == 'json':
                return jsonresponse(f)(**args)

            if ext == 'xml':
                return xmlresponse(f)(**args)

            if ext == 'yaml':
                return yamlresponse(f)(**args)

        return f(**args)

    return wrapper

def jsonresponse(f):
    """Decorate an action to return a JSON format."""
    @wraps(f)
    def wrapper(**args):
        
        response = f(**args)

        body = response
        code = 200
        headers = {}

        if type(response) is tuple:
            if len(response) == 2:
                body, code = response

            if len(response) == 3:
                body, code, headers = response
     
        # convert python object to JSON
        body = json.dumps(body, separators = (',', ':'))

        headers['Content-Encoding'] = 'utf-8'
        headers['Content-Type'] = 'application/json'
        headers['Content-MD5'] = md5.new(body).hexdigest()
        headers['Content-Length'] = len(body.encode('utf-8'))

        return body, code, headers

    return wrapper

def xmlresponse(f):
    """Decorate an action to return an XML format."""
    @wraps(f)
    def wrapper(**args):
        pass

    return wrapper
