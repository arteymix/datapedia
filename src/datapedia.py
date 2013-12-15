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
from difflib import HtmlDiff
import wtforms
import glob
import md5
import os
import json

import forms
from decorators import detectresponse

app = Flask(__name__)

# Data structure in the data (set of required )
DATA_STRUCTURE = {
    'ip': unicode,
    'time': int, 
    'license': unicode, 
    'approvers': list, 
    'sources': list,
    'data': object
}

DATA_PATH = 'data'

DATA_FOLDER_STRUCTURE = {
    'current': {},
    'approving': {},
    'archive': {}
}

SUPPORTED_EXT = ['json']

EXT_STRING_LOADER = {
    'json': lambda s: json.loads(s)
}

EXT_FILE_LOADER = {
    'json': lambda f: json.load(f)
}

EXT_STRING_DUMPER = {
    'json': lambda o: json.dumps(o, separators = (',', ':'))
}

EXT_FILE_DUMPER = {
    'json': lambda o, f: json.dump(o, f, separators = (',', ':')),
}

def generate_folder_structure(destination, structure):
    """
    Recursively generate a data structure
    destination -- folder path from which the structure will be generated
    structure   -- dict defining the folder structure by its keys
    """
    if not os.path.exists(destination):
        os.mkdir(destination)

    for folder in structure:
        d = os.path.join(destination, folder)
        if not os.path.exists(d):
            os.mkdir(d)

        generate_folder_structure(d, structure[folder])

# enforce folder structure
generate_folder_structure(DATA_PATH, DATA_FOLDER_STRUCTURE)

def find_current(name, ext = None):
    """
    Find the path for a given name and extension
    name -- str
    ext  -- str if given, return the corresponding path, otherwise it will seek
    for the path using SUPPORTED_EXT constant.
    """
    if ext == None:
        for ext in SUPPORTED_EXT:
            if os.path.exists(path = find_current(name, ext)):
                return path
 
        ext = SUPPORTED_EXT[0]

    return os.path.join(DATA_PATH, 'current', '{}.{}'.format(name, ext))

def find_timestamped(folder, name, ext = None, timestamp = time()):
    """
    Get the approving path for a given name, ext and time.
    ext       -- str if not given, it will seek for it in 
    timestamp -- int if not given, time() will be used
    """
    timestamp = str(int(timestamp))

    # make a directory in the archives
    d = os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext))

    if not os.path.exists(d):
        os.mkdir(d)

    if ext == None:
        for ext in SUPPORTED_EXT:
            if os.path.exists(path = find_timestamped(name, ext, timestamp)):
                return path

        ext = SUPPORTED_EXT[0]
        
    return os.path.join(d, timestamp)

def find_timestamped_latest(folder, name, ext = None, timestamp = time()):
    """
    Instead of seeking for a precise file, it will find the latest timestamped taking
    the timestamp parameter as an upper bound. This answer the question: 
    What was the data at <timestamp>?
    """
    timestamp = str(int(timestamp))

    # make a directory in the archives
    d = os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext))

def limit(iterator, count):
    while count > 0:
        yield next(iterator)
        count -= 1

@app.route('/')
def datapedia():
    """
    Home page for datapedia.
    """
    search = request.args.get('search', '*')
    dest = os.path.join(DATA_PATH, 'current', search)
    results = ((name, ext[1:]) for (name, ext) in (os.path.splitext(os.path.basename(path)) for path in limit(glob.iglob(dest), 10)))

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

@app.route('/current/<name>', methods = {'GET', 'POST'})
def current(name):
    """ 
    Present the data with an HTML template.
    """
    data = {}
    form = forms.DataForm()

    try:
        with open(find_current(name, 'json'), 'r') as f:
            data = EXT_FILE_LOADER['json'](f)
    except IOError:
            pass

    # load default data
    for field in form:
        field.default = data.get(field.name)

    if request.method in {'POST'}:
        # non regressive to current data
        form.data.validators.append(forms.NotRegressive(data.get('data')))

        if form.validate_on_submit():
            data = {field.name: field.data for field in form if field.name in DATA_STRUCTURE}
            data['ip'] = request.remote_addr
            data['approvers'] = [request.remote_addr]
            data['data'] = form.data.object_data
            # archive it right away
            with open(find_timestamped('archive', name, form.ext.data), 'w') as a, \
                open(find_current(name, form.ext.data), 'w') as f:
                EXT_FILE_DUMPER[form.ext.data](data, f)
                EXT_FILE_DUMPER[form.ext.data](data, a)
   
    return render_template('data.html', name = name, data = data, form = form)

@app.route('/current/<name>.<ext>', methods={'GET', 'POST', 'PUT'})
@detectresponse
def current_raw(name, ext):	
    if request.method in {'POST', 'PUT'}:

        form = forms.RawForm()
        
        try:
            with open(find_current(name, ext), 'r') as f:
                form.data.validators.append(forms.NotRegressive(json.load(f)))
        except IOError as ioe:
            pass

        if not form.validate():
            return {field.name: field.errors for field in form}, 400

        data = {field.name: field.data for field in form if field.name in DATA_STRUCTURE}

        data['ip'] = request.remote_addr

        with open(find_timestamped('archive', name, ext, int(time())), 'w') as a, \
            open(find_current(name, ext)) as f:
            EXT_FILE_DUMPER[ext](a)
            EXT_FILE_DUMPER[ext](f)
   
    try:
        with open(find_current(name, ext), 'r') as f:
            EXT_FILE_LOADER[ext](f)

    except IOError as ioe:
        return ioe.message, 404

@app.route('/approve/<name>(/<int:timestamp>)')
def approve(name, timestamp = None):
    pass

@app.route('/approve/<name>.<ext>(/<int:timestamp>)')
def approve_raw(name, ext, timestamp = None):
    """Approve an approving or current data"""
    if time == None:
        with open(find_current(name, ext), 'rw') as f:
            data = EXT_FILE_LOADER[ext](f)
            if request.remote_addr in data['approvers']:
                return 'You have already approved this data.', 400

            f.seek(0)
            data['approvers'].append(request.remote_addr)
            EXT_FILE_DUMPER[ext](data, f)

            return redirect(url_for('current_raw', name = name, ext = ext))

    with open(find_current(name, ext), 'r+') as f, \
         open(find_timestamped('approving', name, ext, int(time)), 'w') as a:
        data = EXT_FILE_LOADER[ext](f)
        f.seek(0)
        if not request.remote_addr in data['approvers']:
            data['approvers'].append(request.remote_addr)
            EXT_FILE_DUMPER[ext](a)
            EXT_FILE_DUMPER[ext](f)
    
    return redirect(url_for('raw', name = name, ext = ext))

@app.route('/<folder>/<name>.<ext>/<int:timestamp>')
@detectresponse
def timestamped(folder, name, ext, timestamp):
    """
    Display a raw timestamped data from archive or approving folders.
    """
    path = os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext))

    for f in (_ for _ in sorted(os.join(path, '*')) if int(os.path.basename(_)) >= time):
        with open(f) as f:
            return EXT_FILE_LOADER[ext](f)

    else:
        return 'No result older than {} were found.'.format(str(timestamp)), 404

@app.route('/evolution/<name>.<ext>')
@detectresponse
def evolution_raw(name, ext):
    evolution = []
    dest = os.path.join(DATA_PATH, 'archive', '{}.{}'.format(name, ext), '*')
    for path in sorted(glob.iglob(dest)):
        with open(path, 'r') as f:
            evolution.append(EXT_FILE_LOADER[ext](f))
    
    return evolution

@app.route('/evolution/<name>')
def evolution(name):
    htmldiff = HtmlDiff()
    evolution = []
    last_time = 0
    last_lines = []
    d = os.path.join(DATA_PATH, 'archive', '{}.{}'.format(name, 'json'), '*')
    for path in sorted(glob.iglob(d)):
        with open(path, 'r') as f:
            lines = json.dumps(json.load(f), indent = 4, separators = (',', ': '), sort_keys = True).split("\n")
            time = int(os.path.basename(path))
            evolution.append(htmldiff.make_table(last_lines, lines, fromdesc=datetime.fromtimestamp(last_time), todesc=datetime.fromtimestamp(time)))
            last_time, last_lines = time, lines

    return render_template('evolution.html', name = name, evolution = evolution)
		
if __name__ == '__main__':
    app.secret_key = 'ioiu8&((*/io0io@£¢rs9'
    app.run(debug = True)
