#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: s; c-basic-offset: 4; tab-width: 4 -*- 
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
from httplib import responses, METHOD_NOT_ALLOWED, BAD_REQUEST, NOT_FOUND
import wtforms
import glob
import os
import json

import forms
from decorators import detectresponse

app = Flask(__name__)

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
    for the path using app.config['SUPPORTED_EXT'] constant.
    """
    if ext == None:
        for ext in app.config['SUPPORTED_EXT']:
            path = find_current(name, ext)
            if os.path.exists(path):
                return path

        ext = app.config['SUPPORTED_EXT'][0]

    return os.path.join(app.config['DATA_PATH'], 'current', '{}.{}'.format(name, ext))

def find_timestamped(folder, name, ext = None, timestamp = time()):
    """
    Get the approving path for a given name, ext and time.
    ext       -- str if not given, it will seek for it in 
    timestamp -- int if not given, time() will be used
    """
    timestamp = str(int(timestamp))

    if not ext:
        for ext in app.config['SUPPORTED_EXT']:
            path = find_timestamped(folder, name, ext, timestamp)
            if os.path.exists(path):
               return path

        ext = app.config['SUPPORTED_EXT'][0]
        
    d = os.path.join(app.config['DATA_PATH'], folder, '{}.{}'.format(name, ext))

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
        for ext in app.config['SUPPORTED_EXT']:
            path = find_timestamped_latest(folder, name, ext, timestamp)
            if os.path.exists(path):
               return path

    # make a directory in the archives
    d = os.path.join(app.config['DATA_PATH'], folder, '{}.{}'.format(name, ext))

    if not os.path.exists(d):
        os.mkdir(d)

    for path in reversed(sorted(glob.iglob(os.path.join(app.config['DATA_PATH'], folder, '{}.{}', '*')))):
        if int(os.path.basename(path)) <= int(timestamp):
            return path
        
    return os.path.join(app.config['DATA_PATH'], folder, '{}.{}'.format(name, ext), timestamp)

def limit(iterator, count):
    while count > 0:
        yield next(iterator)
        count -= 1
        
@app.template_filter('type')
def _type(obj):
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

@app.before_first_request
def before_first_request():
    generate_folder_structure(app.config['DATA_PATH'], app.config['DATA_FOLDER_STRUCTURE'])

@app.route('/')
def datapedia():
    """
    Home page for datapedia.
    """
    search = request.args.get('search', '')
    dest = os.path.join(app.config['DATA_PATH'], 'current', search if search else '*')

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

    return render_template('datapedia.html', search = search, results = results, example = example)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/current/<name>', methods = {'GET', 'POST'})
@app.route('/current/<name>.<ext>', methods = {'GET', 'POST', 'PUT'})
@detectresponse
def current(name, ext = None):
    """"""
    form = forms.CurrentForm()
     
    if request.method in {'POST', 'PUT'}:
        # resource must not exist if it's a PUT
        if request.method == 'PUT' and os.exists(find_current(name, ext if ext else form.ext.data)):
            message = 'Cannot call PUT, there is already a data at this endpoint.'

            if ext:
                return message, METHOD_NOT_ALLOWED
       
            return render_template('error.html', message = message, code = METHOD_NOT_ALLOWED), METHOD_NOT_ALLOWED

        if request.method == 'POST':
            # non regressive to current data
            try:
                with open(find_current(name, ext if ext else form.ext.data), 'r') as f:
                    d = app.config['FILE_DECODER'][ext if ext else form.ext.data](f)['data']
                    form.data.validators.append(forms.NotRegressive(d))
 
            except:
                message = 'Cannot call POST, there no data at this endpoint.'

                if ext:
                    return message, METHOD_NOT_ALLOWED

                return render_template('error.html', code = METHOD_NOT_ALLOWED, message = message), METHOD_NOT_ALLOWED

        if form.validate_on_submit():
            data = {field.name: field.data for field in form if field.name in app.config['DATA_STRUCTURE']}
            data['ip'] = request.remote_addr
            data['approvers'] = [request.remote_addr]
            data['data'] = form.data.object_data

            timestamp = int(time())

            if request.method == 'PUT':
                with open(find_current(name, ext if ext else form.ext.data), 'w') as f:
                    app.config['FILE_ENCODER'][ext if ext else form.ext.data](data, f)
        
            if request.method == 'POST':
                timestamp = int(time())

                # mark data for approvement
                with open(find_timestamped('approving', name, ext if ext else form.ext.data, timestamp), 'w') as f:
                    app.config['FILE_ENCODER'][ext if ext else form.ext.data](data, f)

                return redirect(url_for('approving', name = name, ext = ext, timestamp = timestamp))             

        elif ext:
            return {field.name: field.errors for field in form}, BAD_REQUEST

    data = None

    try:
        with open(find_current(name, ext), 'r') as f:
            data = app.config['FILE_DECODER'][ext if ext else app.config['SUPPORTED_EXT'][0]](f)

    except IOError as ioe:
        if ext:
            return 'There is no data at this endpoint.', METHOD_NOT_ALLOWED
    
    if ext:
        return data

    return render_template('current.html', name = name, data = data, form = form)

@app.route('/approving/<name>/<int:timestamp>', methods = {'GET', 'POST'}, defaults = {'ext': None})
@app.route('/approving/<name>.<ext>/<int:timestamp>', methods = {'GET', 'POST'})
@detectresponse
def approving(name, ext, timestamp):
    form = forms.ApprovingForm()

    try:
        with open(find_timestamped('approving', name, ext if ext else form.ext.data, timestamp), 'r') as a:
            approving = app.config['FILE_DECODER'][ext if ext else form.ext.data](a)
    except IOError:
        message = 'There is no data at this endpoint.'

        if ext:
            return message, NOT_FOUND

        return render_template('error.html', code = NOT_FOUND, message = message), NOT_FOUND

    if request.method == 'POST':

        # user might have providen an ext, so we update approving
        with open(find_timestamped('approving', name, ext if ext else form.ext.data, timestamp), 'r') as a:
            approving = app.config['FILE_DECODER'][ext if ext else form.ext.data](a)

        if not request.remote_addr in approving['approvers']:
            approving['approvers'].append(request.remote_addr)

        if form.validate():
            # update approving
            with open(find_timestamped('approving', name, ext if ext else form.ext.data, timestamp), 'w') as a:
                app.config['FILE_ENCODER'][ext if ext else form.ext.data](approving, a)

            try:
                with open(find_current(name, ext), 'r') as c:
                    current = app.config['FILE_DECODER'][ext if ext else form.ext.data](c)
                    
                if len(approving['approvers']) > len(current['approvers']):
                    with open(find_current(name, ext), 'w') as c, open(find_timestamped('archive', name, ext), 'w')as a:
                        # write to archive and replace current
                        app.config['FILE_ENCODER'][ext if ext else form.ext.data](approving, a)
                        app.config['FILE_ENCODER'][ext if ext else form.ext.data](approving, c)

                    # remove approving
                    os.remove(find_timestamped('approving', name, ext if ext else form.ext.data, timestamp))

                    return redirect(url_for('current', name = name, ext = ext))

            except IOError:
                # no current found, write it
                with open(find_current(name, ext), 'w') as c,  open(find_timestamped('archive', name, ext), 'w'):
                    app.config['FILE_ENCODER'][ext if ext else form.ext.data](approving, a)
                    app.config['FILE_ENCODER'][ext if ext else form.ext.data](approving, c)
                    os.remove(find_timestamped('approving', name, ext, timestamp))
  
                    return redirect(url_for('current', name, ext))
    elif ext:
        return {field.name: field.errors for field in form}, BAD_REQUEST

    if ext:
        return approving

    # compute the delta between approved and current
    with open(find_current(name, 'json'), 'r') as f:
        htmldiff = HtmlDiff()
        current = json.load(f)
        diff = htmldiff.make_table(fromlines = json.dumps(current, indent = 4).splitlines(), tolines = json.dumps(approving, indent = 4).splitlines())
        return render_template('approving.html', name = name, approving = approving, timestamp = timestamp, diff = diff, current = current, form = form)

    return render_template('approving.html', name = name, approving = approving, timestamp = timestamp, diff = None, current = current, form = form)

@app.route('/approvings/<name>')
@app.route('/approvings/<name>.<ext>')
@detectresponse
def approvings(name, ext = None):
    approvings = {os.path.basename(f): app.config['FILE_DECODER'][ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(app.config['DATA_PATH'], 'approving', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return approvings
 
    return render_template('approvings.html', name = name, approvings = approvings)

@app.route('/archive/<name>', defaults = {'ext':  None, 'timestamp': 0})
@app.route('/archive/<name>/<int:timestamp>', defaults = {'ext': None})
@app.route('/archive/<name>.<ext>', defaults = {'timestamp': 0})
@app.route('/archive/<name>.<ext>/<int:timestamp>')
@detectresponse
def archive(name, ext, timestamp):
    """"""
    try:
        with open(find_timestamped_latest('archive', name, ext, timestamp), 'r') as f:
            archive = app.config['FILE_DECODER'][ext if ext else app.config['SUPPORTED_EXT'][0]](f)

    except IOError as ioe:
        message = ''

        if ext:
            return message, NOT_FOUND

        return render_template('error.html', code = NOT_FOUND, message = message)

    if ext:
        return archive

    return render_template('archive.html', name = name, archive = archive, timestamp = timestamp)

@app.route('/archives/<name>')
@app.route('/archives/<name>.<ext>')
@detectresponse
def archives(name, ext = None):
    archives = {os.path.basename(f): app.config['FILE_DECODER'][ext if ext else 'json'](open(f, 'r')) for f in glob.iglob(os.path.join(app.config['DATA_PATH'], 'archive', '{}.{}'.format(name, ext if ext else 'json'), '*'))}
    
    if ext:
        return archives

    # compute diff from one to another
    htmldiff = HtmlDiff()
    archives = {}
    last_time = 0
    last_lines = []
    d = os.path.join(app.config['DATA_PATH'], 'archive', '{}.{}'.format(name, 'json'), '*')
    for path in sorted(glob.iglob(d)):
        with open(path, 'r') as f:
            lines = json.dumps(json.load(f), indent = 4, separators = (',', ': '), sort_keys = True).split("\n")
            time = int(os.path.basename(path))
            archives[time] = htmldiff.make_table(last_lines, lines, fromdesc=datetime.fromtimestamp(last_time), todesc=datetime.fromtimestamp(time))
            last_time, last_lines = time, lines

    return render_template('archives.html', name = name, archives = archives)
		
if __name__ == '__main__':
    app.config.from_object('config.DevelopmentConfig')
    app.run(debug = True)
