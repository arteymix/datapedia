# -*- Mode: Python; coding: utf-8; indent-tabs-mode: s; c-basic-offset: 4; tab-width: 4 -*- 
import tempfile
import json

class Config(object):
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

    STRING_DECODER = {
        'json': lambda s: json.loads(s)
    }

    FILE_DECODER = {
        'json': lambda f: json.load(f)
    }

    STRING_ENCODER = {
        'json': lambda o: json.dumps(o, separators = (',', ':'))
    }

    FILE_ENCODER = {
        'json': lambda o, f: json.dump(o, f, separators = (',', ':'))
    }

    SECRET_KEY = 'ioiu8&((*/io0iors9'

class DevelopmentConfig(Config):
    pass

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    DATA_PATH = tempfile.mkdtemp()
