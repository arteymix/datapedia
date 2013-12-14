#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- 
#
# main.py
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

from flask import Flask, request, render_template, redirect, url_for
from time import time
from datetime import datetime
from functools import wraps
from itertools import izip_longest
import wtforms
import glob
import md5
import os
import json
import difflib

import forms

app = Flask(__name__)

# Data structure in the data (set of required )
DATA_STRUCTURE = {
    'ip': str,
    'time': int, 
    'license': str, 
    'approvers': list, 
    'sources': list,
    'data': object
}

def limit(iterable, count):
    """
    Limit number of iterated elements from an iterable.
    count -- is the maximum number of elements to iterate through
    """
    while count > 0:
        yield next(iterable)
        count -= 1

def find_data(name, ext):
    """
    Get the data path for a given name and ext.
    """

    return 'data/{}.{}'.format(name, ext)

def find_archive(name, ext, time):
    """
    Get the archive path for a given name, ext and time.
    """
    # make a directory in the archives
    if not os.path.isdir('archives/{}.{}'.format(name, ext)):
        os.mkdir('archives/{}.{}'.format(name, ext))

    return 'archives/{}.{}/{}'.format(name, ext, str(time))

def jsonresponse(f):
    """
    Decorate an action to return a JSON format.
    """
    @wraps(f)
    def wrapper(**args):
        
        response = f(**args)

        body = response
        code = 200
        headers = {}

        if type(response) == tuple:

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

def xmlresponse(f, **xmlargs):
    """Decorate an action to return an XML format."""

    @wraps(f)
    def wrapper(**args):
        return f(**args)

def ymlresponse(f):
    """Decorate an action to return an YML format."""

    @wraps(f)
    def wrapper(**args):
        return f(**args)

# ensure archives and data folder exist
if not os.path.exists('archives'):
    os.mkdir('archives')

if not os.path.exists('data'):
    os.mkdir('data')

@app.route('/')
def datapedia():
    """
    Home page for datapedia.
    """
    search = request.args.get('search', '*')
    results = ((name, ext[1:]) for (name, ext) in (os.path.splitext(os.path.basename(path)) for path in limit(glob.iglob('data/' + search), 10)))

    example = {
        'time': int(time()), 
        'license': 'CC BY', 
        'data': [1, 2, 3], 
        'sources' : ['http://datapedia.org/example'],
        'approvers': ['127.0.0.1'],
        'ip': '127.0.0.1'
    }

    return render_template('datapedia.html', search = search, results = results, structure = DATA_STRUCTURE, example = example)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/developers')
def developers():
    return render_template('developers.html')

@app.route('/data/<name>', methods = {'GET', 'POST'})
def data(name):
    """ 
    Present the data with an HTML template.
    """
    form = forms.DataForm()

    # load default data
    try:
        with open(find_data(name, 'json'), 'r') as f:
            data = json.load(f)
            for field in form:
                field.default = data.get(field.name)
    except IOError:
            pass

    if request.method in {'POST'}:

        # non-regressive validation
        form.data.validators.append(forms.non_regressive(form.data.default))
        
        data = {field.name: field.data for field in form if field.name in DATA_STRUCTURE}

        if form.validate_on_submit():
            # archive it right away
            with open(find_archive(name, form.ext.data, int(time())), 'w') as f:
                json.dump(data, f, separators=(',', ':'))

            # replace the main file
            with open(find_data(name, form.ext.data), 'w') as f:	
                json.dump(data, f, separators=(',', ':'))
   
    return render_template('data.html', name = name, form = form)

@app.route('/data/<name>.<ext>', methods={'GET', 'POST', 'PUT'})
@jsonresponse
def raw(name, ext):	
    if request.method in {'POST', 'PUT'}:

        form = forms.RawForm()

        data = {field.name: field.data for field in form if field.name in DATA_STRUCTURE}

        with open(find_data(name, ext), 'r') as f:
            try:
                form.data.validators.append(forms.non_regressive(json.load(f)))
            except IOError as ioe:
                # no data to validate against
                app.logger.info(ioe)

        if not form.validate_on_submit():
            # return errors
            return {field.name: field.errors for field in form}, 400

        # archive it right away
        with open(find_archive(name, ext, int(time())), 'w') as f:
            json.dump(data, f, separators=(',', ':'))

        # replace the main file
        with open(find_data(name, ext), 'w') as f:	
            json.dump(data, f, separators=(',', ':'))
   
    try:
        with open(find_data(name, ext), 'r') as f:
            if ext == 'json':
                return json.load(f)

            if ext == 'xml':
                return xml.parse(f)

            if ext == 'yaml':
                return yaml

    except IOError as ioe:
        app.logger.error(ioe)
        return ioe.message, 404

@app.route('/approve/<name>.<ext>')
def approve(name, ext):
    with open(find_data(name, ext), 'r+') as f, \
         open(find_archive(name, ext, int(time)), 'w') as a:
        data = json.load(f)
        f.seek(0)
        if not request.remote_addr in data['approvers']:
            data['approvers'].append(request.remote_addr)
            json.dump(data, a, separators = (',', ':'))
            json.dump(data, f, separators = (',', ':'))
    
    return redirect(url_for('raw', name = name, ext = ext))

@app.route('/data/<name>.<ext>/<int:time>')
@jsonresponse
def archive(name, ext, time):
    """
    Display a raw timestamped data.
    """
    for f in (_ for _ in sorted(glob.iglob('archives/{}.{}/*'.format(name, ext))) if int(os.path.basename(_)) >= time):
        with open(f) as f:
            if ext == 'json':
                return json.load(f)

            if ext == 'xml':
                pass

            if ext == 'yml':
                pass

    else:
        return 'No result older than {} were found.'.format(str(time)), 404

@app.route('/evolution/<name>.<ext>')
@jsonresponse
def raw_evolution(name, ext):
    evolution = []
    for path in sorted(glob.iglob('archives/{}.{}/*'.format(name, ext))):
        with open(path, 'r') as f:
            try:
                evolution.append(json.load(f))
            except ValueError as ve:
                app.logger.error(ve)
    
    return evolution

@app.route('/evolution/<name>')
def evolution(name):
    evolution = []
    last_time = 0
    last_lines = []
    for path in sorted(glob.iglob('archives/{}.json/*'.format(name))):
        with open(path, 'r') as f:
            try:
                lines = json.dumps(json.load(f), indent = 4, separators = (',', ': '), sort_keys = True).split("\n")
                time = int(os.path.basename(path))
                evolution.append(difflib.unified_diff(last_lines, lines, fromfiledate=datetime.fromtimestamp(last_time), tofiledate=datetime.fromtimestamp(time)))
                last_time, last_lines = time, lines
            except ValueError as ve: # happens when json objects cannot be decoded (corrupted files)
                app.logger.error(ve)

    return render_template('evolution.html', name = name, evolution = evolution)
		
if __name__ == '__main__':
    app.secret_key = 'ioiu8&((*/io0io@£¢rs9'
    app.run(debug = True)
