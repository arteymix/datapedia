#!/usr/bin/python
#
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: s; c-basic-offset: 4; tab-width: 4 -*- 
#
# Copyright (C) 2013 Guillaume Poirier-Morency <guillaumepoiriermorency@gmail.com>
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
from httplib import responses, METHOD_NOT_ALLOWED, BAD_REQUEST, NOT_FOUND
from functools import wraps
from werkzeug.routing import UnicodeConverter, ValidationError
from distutils.versionpredicate import VersionPredicate
from distutils.version import StrictVersion
import wtforms
import glob
import os
import json

import forms
import converters
from iterators import limit
from decorators import detectresponse

app = Flask(__name__)

# setup converters
app.url_map.converters['extension'] = converters.ExtensionConverter
app.url_map.converters['name'] = converters.NameConverter
app.url_map.converters['version'] = converters.VersionConverter
app.url_map.converters['timestamp'] = converters.TimestampConverter
        
@app.template_filter('type')
def _type(obj):
    """Convert an object to its type"""
    return type(obj)

@app.template_filter('toprettyjson')
def toprettyjson(obj):
    return json.dumps(obj, separators = (', ', ': '),indent = 4)

@app.template_filter('tohttpstatus')
def tohttpstatus(code):
    """Return the HTTP status related to a given code"""
    return responses[code]

@app.template_filter('todatetime')
def todatetime(time):
    return datetime.fromtimestamp(float(time))

@app.template_filter('todate')
def todate(time):
    return datetime.date.fromtimestamp(float(time))

@app.errorhandler(NOT_FOUND)
def not_found(e):
    return render_template('error.html', message = e.message, code = NOT_FOUND)

@app.before_first_request
def before_first_request():
    generate_folder_structure(app.config['DATA_FOLDER_PATH'], \
        app.config['DATA_FOLDER_STRUCTURE'])

@app.route('/')
def datapedia():
    """Home page for datapedia."""
    search = request.args.get('search', '')
    dest = os.path.join(app.config['DATA_FOLDER_PATH'], 'current', search if search else '*')

    # check if it matches exactly an entry
    name, ext = os.path.splitext(search)
    
    if not ext:
       ext = None
    else:
       ext = ext[1:]

    path, _ = find_current(name, ext)

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

    with open('datapedia/static/js/ajax-example.js') as f:
        ajax_example = f.read()

    return render_template('datapedia.html', search = search, results = results, example = example, \
        ajax_example = ajax_example)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/current/<name>', methods = {'GET', 'POST'}, defaults = {'version': None})
@app.route("/<version('== 1.0.0'):version>/current/<name>.<extension:ext>", methods = {'GET', 'POST', 'PUT'})
@detectresponse
def current(version, name, ext = None):
    """"""
    if ext is None:
        ext = app.config['DEFAULT_EXTENSION']

    form = forms.CurrentForm()

    current_path, current_ext = find_current(name, ext.extension)
        
    # enforce PUT on existing data
    if request.method == 'PUT' and ext and os.path.exists(current_path):
        return 'Cannot call PUT, there is already a data at this endpoint.', METHOD_NOT_ALLOWED

    if request.method == 'POST':
        if os.path.exists(current_path):
            # non regressive to current data
            with open(current_path, 'r') as current:
                data = ext.load(current)
                form.data.validators.append(forms.NotRegressive(data['data']))

        # enforce POST when no data exist (api only)
        elif ext:
            message = 'Cannot call POST, there no data at this endpoint.'
            if ext:
                return message, METHOD_NOT_ALLOWED

    if request.method in {'POST', 'PUT'}:
        if form.validate_on_submit():
            data = {field.name: field.data for field in form if field.name in app.config['DATA_STRUCTURE']}
            data['ip'] = request.remote_addr
            data['approvers'] = [request.remote_addr]
            data['data'] = form.data.object_data
            data['timestamp'] = int(time())

            if os.path.exists(current_path):
                # mark data for approvement
                approving_path, approving_ext, approving_timestamp = find_approving(name, current_ext, data['timestamp'])

                with open(approving_path, 'w') as approving:
                    ext.dump(data, approving)

                return redirect(url_for('approving', name = name, ext = ext, timestamp = approving_timestamp))             
            else:            
                # first data supplied!
                with open(current_path, 'w') as current:
                    ext.dump(data, current)
         
        # not valid data
        elif ext:
            return {field.name: field.errors for field in form}, BAD_REQUEST

        else:
            return render_template('current.html', name = name, form = form)

    # GET
    try:
        with open(current_path, 'r') as f:
            data = ext.load(f)
            if version:
                return data

            return render_template('current.html', name = name, data = data, form = form)
  
    except IOError:
        message = 'There is no data at this endpoint.'
        if ext:
            return 'There is no data at this endpoint.', NOT_FOUND

        # propose creation
        return render_template('current.html', name = name, form = form), NOT_FOUND

@app.route('/approving/<name>/<int:timestamp>', methods = {'GET', 'POST'}, defaults = {'version': None, 'ext': None})
@app.route("/<version('== 1.0.0'):version>/approving/<name>.<extension:ext>/<int:timestamp>", methods = {'GET', 'POST'})
@detectresponse
def approving(version, name, ext, timestamp):
    form = forms.ApprovingForm()

    approving_path, approving_ext, _ = find_approving(name, ext if ext else form.ext.data, timestamp)

    if not os.path.exists(approving_path):
        if ext:
            return 'There is no data at this endpoint.', NOT_FOUND

        return render_template('error.html', code = NOT_FOUND, message = message), NOT_FOUND

    with open(approving_path, 'r') as a:
        approving = app.config['FILE_DECODER'][approving_ext](a)

    current_path, current_ext = find_current(name, approving_ext)

    with open(current_path, 'r') as c:
        current = app.config['FILE_DECODER'][current_ext](c)

    if request.method == 'POST':
        if request.remote_addr in approving['approvers']:
            return 'You have already approved this data', BAD_REQUEST

        approving['approvers'].append(request.remote_addr)

        # not regressive validation
        form.data = JSONTextAreaField()
        form.data.validators.append(NotRegressive(current))

        if form.validate_on_submit():
            # update approving
            with open(approving_path, 'w') as a:
                app.config['FILE_ENCODER'][approving_ext](approving, a)
                    
            archive_path, archive_ext, archive_timestamp = find_archive(name, ext, timestamp)

            # check if the approving version has more approvers than the current version
            if len(approving['approvers']) > len(current['approvers']):
                with open(current_path, 'w') as c, open(archive_path, 'w')as a:
                    # write to archive and replace current
                    app.config['FILE_ENCODER'][archive_ext](approving, a)
                    app.config['FILE_ENCODER'][current_ext](approving, c)

                # remove approving
                os.remove(approving_path)

                return redirect(url_for('current', name = name, ext = ext))

        elif ext:
            return {field.name: field.errors for field in form}, BAD_REQUEST

    if ext:
        return approving

    # compute the delta between approved and current
    htmldiff = HtmlDiff()
    approving_lines = json.dumps(approving, indent = 4).splitlines()
    current_lines = json.dumps(current, indent = 4).splitlines()
    diff = htmldiff.make_table(fromlines = current_lines, tolines = approving_lines)

    return render_template('approving.html', name = name, approving = approving, timestamp = timestamp, diff = diff, current = current, form = form)

@app.route('/approvings/<name>', defaults = {'version': None})
@app.route("/<version('== 1.0.0'):version>/approvings/<name>.<extension:ext>")
@detectresponse
def approvings(version, name, ext = None):
    approvings = {os.path.basename(f): app.config['FILE_DECODER'][ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(app.config['DATA_FOLDER_PATH'], 'approving', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return approvings
 
    return render_template('approvings.html', name = name, approvings = approvings)

@app.route('/archive/<name>(/<timestamp:timestamp>)', defaults = {'version': None})
@app.route("/<version('== 1.0.0'):version>/archive/<name>.<extension:ext>(/<timestamp:timestamp>)")
@detectresponse
def archive(version, name, ext = None, timestamp = 0):
    """"""
    try:
        with open(find_archive(name, ext, timestamp), 'r') as f:
            archive = app.config['FILE_DECODER'][ext if ext else app.config['SUPPORTED_EXT'][0]](f)

    except IOError as ioe:
        message = 'No archive with name {} could be found.'.format(name)

        if ext:
            return message, NOT_FOUND

        return render_template('error.html', code = NOT_FOUND, message = message)

    if ext:
        return archive

    return render_template('archive.html', name = name, archive = archive, timestamp = timestamp)

@app.route('/archives/<name>', defaults = {'version': None})
@app.route("/<version('== 1.0.0'):version>/archives/<name>.<extension:ext>")
@detectresponse
def archives(version, name, ext = None):
    archives = {os.path.basename(f): app.config['FILE_DECODER'][ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(app.config['DATA_FOLDER_PATH'], 'archive', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return archives

    # compute diff from one to another
    htmldiff = HtmlDiff()
    archives = {}
    last_time = 0
    last_lines = []
    d = os.path.join(app.config['DATA_FOLDER_PATH'], 'archive', '{}.{}'.format(name, 'json'), '*')
    for path in sorted(glob.iglob(d)):
        with open(path, 'r') as f:
            lines = json.dumps(json.load(f), indent = 4, separators = (',', ': '), sort_keys = True).split("\n")
            time = int(os.path.basename(path))
            archives[time] = htmldiff.make_table(last_lines, lines, fromdesc=datetime.fromtimestamp(last_time), todesc=datetime.fromtimestamp(time))
            last_time, last_lines = time, lines

    return render_template('archives.html', name = name, archives = archives)
	
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

# utilities 

def find_current(name, ext = None):
    """
    Find the path for a given name and extension
    name -- str
    ext  -- str if given, return the corresponding path, otherwise it will seek
    for the path using app.config['SUPPORTED_EXT'] constant.
    """
    folder = os.path.join(app.config['DATA_FOLDER_PATH'], 'current')

    if not ext:
        for ext in app.config['EXTENSIONS']:
            path, ext = find_current(name, ext)

            if os.path.exists(path):
                return path, ext

        ext = app.config['DEFAULT_EXTENSION']

    return os.path.join(folder, '{}.{}'.format(name, ext)), ext

def find_timestamped(folder, name, ext = None, timestamp = time()):
    """
    Get the approving path for a given name, ext and time.

    folder    -- str
    name      -- str
    ext       -- str if given, it will seek specifically for this format
    timestamp -- int if not given, time() will be used
    """
    timestamp = int(timestamp)

    folder = os.path.join(app.config['DATA_FOLDER_PATH'], folder)

    if not ext:
        for ext in app.config['EXTENSIONS']:
            path, ext, timestamp = find_timestamped(folder, name, ext, timestamp)

            if os.path.exists(path):
               return path, ext, timestamp

        # no ext found
        ext = app.config['DEFAULT_EXTENSION']

    folder = os.path.join(folder, '{}.{}'.format(name, ext))

    if not os.path.exists(folder):
        os.mkdir(folder)

    return os.path.join(folder, str(timestamp)), ext, timestamp

def find_approving(name, ext = None, timestamp = time()):
    return find_timestamped('approving', name, ext, timestamp)

def find_archive(name, ext = None, timestamp = time()):
    pass
