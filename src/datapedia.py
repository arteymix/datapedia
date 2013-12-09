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

from flask import Flask, request, render_template
from time import time
from datetime import datetime
import glob
import md5
import os
import json
import difflib

app = Flask(__name__)

def limit(iterable, count):
    while count > 0:
        yield next(iterable)
        count -= 1

if not os.path.exists('archives'):
    os.mkdir('archives')

if not os.path.exists('data'):
    os.mkdir('data')

@app.route('/')
def home():
    results = (os.path.basename(path) for i, path in enumerate(glob.iglob('data/' + request.args.get('search', '*'))) if i < 10)
    return render_template('home.html', results=results)

@app.route('/<name>')
def datapedia(name):
    # present the file with a template
    try:
        with open('data/' + name + '.json', 'r') as f:
            return render_template('datapedia.html', name=name, data=json.load(f))
    except IOError:
        app.logger.info('No data for {} was found, proposing creation.', name)
        return render_template('datapedia.html', name=name, data=None)

@app.route('/<name>.<ext>', methods={'GET', 'POST', 'PUT'})
def raw(name, ext):	
    if request.method in {'POST', 'PUT'}:
	    # write headers info
        data = {}

        data['time'] = int(time())
        data['approvers'] = []
        data['ip'] = request.remote_addr
        data['license'] = request.form['license'] # string
        data['sources'] = request.form.get('sources', []) # array of urls
        try:
            data['data'] = json.loads(request.form['data']) # json-encoded data
        except ValueError as ve:
            app.logger.error(ve)
            return 'Data could not be decoded.', 400

        # validation
        try:
            assert 'license' in data
        except AssertionError:
            return 'Data are not valid.', 400
    
        # make a directory in the archives
        if not os.path.isdir('archives/' + name + '.' + ext):
            os.mkdir('archives/' + name + '.' + ext)

        # archive it right away
        with open('archives/' + name + '.' + ext + '/' + str(int(time())), 'w') as f:
            json.dump(data, f, separators=(',', ':'))

        # replace the main file
        with open('data/' + name + '.' + ext, 'w') as f:	
            json.dump(data, f, separators=(',', ':'))

    try:
        with open('data/' + name + '.' + ext, 'r') as f:
            body = f.read()

            headers = {}
            headers['Content-Encoding'] = 'utf-8'
            headers['Content-Type'] = 'application/json'
            headers['Content-MD5'] = md5.new(body).hexdigest()
            headers['Content-Length'] = len(body.encode('utf-8'))

            return body, 200, headers

    except IOError:
        return 'No data named ' + name + ' was found.', 404

@app.route('/<name>.<ext>/<int:time>')
def archive(name, ext, time):
    for f in sorted(glob.iglob('archives/' + name + '.' + ext + '/*')):
        if int(os.path.basename(f)) >= time:
            with open(f) as f:
                body = f.read()

                headers = {}
                headers['Content-Encoding'] = 'utf-8'
                headers['Content-Type'] = 'application/json'
                headers['Content-MD5'] = md5.new(body).hexdigest()
                headers['Content-Length'] = len(body.encode('utf-8'))

                return body, 200, headers

    return 'No result older than ' + str(time) + ' were found.', 404

@app.route('/<name>.<ext>/evolution')
def raw_evolution(name, ext):
    evolution = []
    for path in sorted(glob.iglob('archives/{}.{}/*'.format(name, ext))):
        with open(path, 'r') as f:
            try:
                evolution.append(json.load(f))
            except ValueError as ve:
                app.logger.error(ve)

    body = json.dumps(evolution, separators = (',', ':'))

    headers = {}
    headers['Content-Encoding'] = 'utf-8'
    headers['Content-Type'] = 'application/json'
    headers['Content-MD5'] = md5.new(body).hexdigest()
    headers['Content-Length'] = len(body.encode('utf-8'))

    return body, 200, headers

@app.route('/<name>/evolution')
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
		
if __name__ == "__main__":
    app.run(debug = True)


