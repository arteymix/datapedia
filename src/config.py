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
