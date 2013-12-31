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
import tempfile
import json

from utilities import Extension

class Config(object):
    """Base configuration for Datapedia."""
    # Data structure in the data (set of required )
    DATA_STRUCTURE = {
        'ip': unicode,
        'timestamp': int, 
        'license': unicode, 
        'approvers': list, 
        'sources': list,
        'data': object
    }

    DATA_FOLDER_PATH = 'data'

    DATA_FOLDER_STRUCTURE = {
        'current': {},
        'approving': {},
        'archive': {}
    }

    EXTENSIONS = {
        'json': Extension('json', lambda s: json.loads(s), lambda o: json.dumps(o, separators = (',', ':'))),
    }

    DEFAULT_EXTENSION = EXTENSIONS['json']

    SECRET_KEY = 'ioiu8&((*/io0iors9'

    VERSION = '1.0.0'

class DevelopmentConfig(Config):
    """Development configuration for Datapedia."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration for Datapedia."""
    pass

class TestingConfig(Config):
    """Testing configuration for Datapedia."""
    DATA_FOLDER_PATH = tempfile.mkdtemp()
