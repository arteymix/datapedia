from unittest import TestCase
import json
import tempfile

from datapedia.utilities import Extension

class UtilitiesTest(TestCase):

    def test_Extension(self):
        ext = Extension('json', json.load, json.dump)

        self.assertEquals(ext.extension, 'json')

        self.assertEquals(ext.loads('{}'), json.loads('{}'))

        self.assertEquals(ext.dumps({}), json.dumps({}))

        filepath = tempfile.mktemp()
        
        with open(filepath, 'w') as f:
            ext.dumps(obj, f)

        self.assertTrue(os.path.exists(filepath))

        # load from file
        with open(filepath, 'r') as f:
            self.assertEquals(ext.loads(f), json.loads(f))
