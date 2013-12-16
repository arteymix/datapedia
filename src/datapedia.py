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
        app.logger.warning('Creating the missing folder {}.')
        os.mkdir(destination)

    for folder in structure:
        generate_folder_structure(os.path.join(destination, folder), structure[folder])

def find_current(name, ext = None):
    """
    Find the path for a given name and extension
    name -- str
    ext  -- str if given, return the corresponding path, otherwise it will seek
    for the path using SUPPORTED_EXT constant.
    """
    if ext == None:
        for ext in SUPPORTED_EXT:
            path = find_current(name, ext)
            if os.path.exists(path):
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

    if not ext:
        for ext in SUPPORTED_EXT:
            path = find_timestamped(folder, name, ext, timestamp)
            if os.path.exists(path):
               return path

        ext = SUPPORTED_EXT[0]
        
    d = os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext))

    if not os.path.exists(d):
        os.mkdir(d)

    return os.path.join(d, timestamp)

def find_timestamped_latest(folder, name, ext = None, timestamp = time()):
    """
    Instead of seeking for a precise file, it will find the latest timestamped taking
    the timestamp parameter as an upper bound. This answer the question: 
    What was the data at <timestamp>?
    """
    timestamp = str(int(timestamp))

    if not ext:
        for ext in SUPPORTED_EXT:
            path = find_timestamped_latest(folder, name, ext, timestamp)
            if os.path.exists(path):
               return path

    # make a directory in the archives
    d = os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext))

    if not os.path.exists(d):
        os.mkdir(d)

    for path in reversed(sorted(glob.iglob(os.path.join(DATA_PATH, folder, '{}.{}', '*')))):
        if int(os.path.basename(path)) <= int(timestamp):
            return path
        
    return os.path.join(DATA_PATH, folder, '{}.{}'.format(name, ext), timestamp)

def limit(iterator, count):
    while count > 0:
        yield next(iterator)
        count -= 1

@app.before_first_request
def before_first_request():
    generate_folder_structure(DATA_PATH, DATA_FOLDER_STRUCTURE)

@app.route('/')
def datapedia():
    """
    Home page for datapedia.
    """
    search = request.args.get('search', '')
    dest = os.path.join(DATA_PATH, 'current', search if search else '*')

    # check if it matches exactly an entry
    name, ext = os.path.splitext(search)
    
    if not ext:
       ext = None
    else:
       ext = ext[1:]

    path = find_current(name, ext)
    if os.path.exists(path):
        return redirect(url_for('current', name = name, ext = ext))

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
@app.route('/current/<name>.<ext>', methods = {'GET', 'POST', 'PUT'})
@detectresponse
def current(name, ext = None):
    """"""
    form = forms.CurrentForm()

    if request.method in {'POST', 'PUT'}:
        # non regressive to current data
        try:
            with open(find_current(name), 'r') as f:
                d = EXT_FILE_LOADER[ext if ext else request.form['ext']](f)['data']
                form.data.validators.append(forms.NotRegressive(d))

        except IOError:
            pass

        if form.validate_on_submit():
            data = {field.name: field.data for field in form if field.name in DATA_STRUCTURE}
            data['ip'] = request.remote_addr
            data['approvers'] = [request.remote_addr]
            data['data'] = form.data.object_data

            timestamp = int(time())

            with open(find_timestamped('approving', name, form.ext.data, timestamp), 'w') as f:
                EXT_FILE_DUMPER[form.ext.data](data, f)

            return redirect(url_for('approving', name = name, ext = ext, timestamp = timestamp))             
    data = None

    try:
        with open(find_current(name, ext), 'r') as f:
            data = EXT_FILE_LOADER[ext if ext else 'json'](f)

    except IOError as ioe:
        if ext:
            return ioe.message, 404
    
    if ext:
        return data

    return render_template('current.html', name = name, data = data, form = form)

@app.route('/approving/<name>/<int:timestamp>', methods = {'GET', 'POST'}, defaults = {'ext': None})
@app.route('/approving/<name>.<ext>/<int:timestamp>', methods = {'GET', 'POST'})
@detectresponse
def approving(name, ext, timestamp):
    if request.method == 'POST':
        form = ApprovingForm()

        with open(find_timestamped('approving', name, ext, timestamp), 'r+') as a:
            data = EXT_FILE_LOADER[ext if ext else request.form['ext']](a)

            if not request.remote_addr in data['approvers']:
                data['approvers'].append(request.remote_addr)

            try:
                with open(find_current(name, ext), 'r') as c:
                    current_data = EXT_FILE_LOADER[ext if ext else request.form['ext']](c)

                    if len(data['approvers']) > len(current_data['approvers']):
                        EXT_FILE_DUMPER[ext if ext else request.form['ext']](data, f)

                        # current is replaced
                        return redirect(url_for('current', name, ext))
             
                    f.seek(0)

                    # dump it into approvings
                    EXT_FILE_DUMPER[ext if ext else request.form['ext']](data, a)

            except IOError: # current data does not exists, we create it
                with open(find_current(name, ext), 'w') as f:
                    EXT_FILE_DUMPER[ext if ext else request.form['ext']](data, c)
                    return redirect(url_for('current', name, ext))
    
    data = None

    try:
        with open(find_timestamped('approving', name, None, timestamp)) as f:
            data = EXT_FILE_LOADER[ext if ext else 'json'](f)

    except IOError as ioe:
        if ext:
            return ioe.message, 404

    if ext:
        return data

    return render_template('approving.html', name = name, data = data, timestamp = timestamp)

@app.route('/approvings/<name>', defaults = {'ext': None, 'timestamp': 0})
@app.route('/approvings/<name>/<int:timestamp>', defaults = {'ext': None})
@app.route('/approvings/<name>.<ext>', defaults = {'timestamp': 0})
@app.route('/approvings/<name>.<ext>/<int:timestamp>')
@detectresponse
def approvings(name, ext, timestamp):
    approvings = {os.path.basename(f): EXT_FILE_LOADER[ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(DATA_PATH, 'approving', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return approvings
 
    return render_template('approvings.html', name = name, approvings = approvings, timestamp = timestamp)

@app.route('/archive/<name>', defaults = {'ext':  None, 'timestamp': 0})
@app.route('/archive/<name>/<int:timestamp>', defaults = {'ext': None})
@app.route('/archive/<name>.<ext>', defaults = {'timestamp': 0})
@app.route('/archive/<name>.<ext>/<int:timestamp>')
@detectresponse
def archive(name, ext, timestamp):
    try:
        with open(find_timestamped_latest('archive', name, ext, timestamp)) as f:
            data = EXT_FILE_LOADER[ext if ext else SUPPORTED_EXT[0]](f)

            if ext:
                return data

            return render_template('archive.html', name = name, data = data, timestamp = timestamp)

    except IOError as ioe:
        return render_template('archive.html', name = name), 404

@app.route('/archives/<name>', defaults = {'ext': None})
@app.route('/archives/<name>/<int:timestamp>', defaults = {'ext': None})
@app.route('/archives/<name>.<ext>')
@app.route('/archives/<name>.<ext>/<int:timestamp>')
@detectresponse
def archives(name, ext, timestamp = 0):
    archives = {os.path.basename(f): EXT_FILE_LOADER[ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(DATA_PATH, 'archive', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return archives

    htmldiff = HtmlDiff()
    archives = {}
    last_time = 0
    last_lines = []
    d = os.path.join(DATA_PATH, 'archive', '{}.{}'.format(name, 'json'), '*')
    for path in sorted(glob.iglob(d)):
        with open(path, 'r') as f:
            lines = json.dumps(json.load(f), indent = 4, separators = (',', ': '), sort_keys = True).split("\n")
            time = int(os.path.basename(path))
            archives[time] = htmldiff.make_table(last_lines, lines, fromdesc=datetime.fromtimestamp(last_time), todesc=datetime.fromtimestamp(time))
            last_time, last_lines = time, lines

    return render_template('archives.html', name = name, archives = archives)
		
if __name__ == '__main__':
    app.secret_key = 'ioiu8&((*/io0io@£¢rs9'
    app.run(debug = True)
