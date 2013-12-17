from unittest import TestCase
from time import time
import os
import tempfile
import json

from src.datapedia import app

class DatapediaTest(TestCase):
    """Test the endpoints of Datapedia"""

    def setUp(self):
        app.config['DATA_PATH'] = tempfile.mkdtemp()
        self.client = app.test_client()

    def tearDown(self):
        os.rmdir(app.config['DATA_PATH'])
 
    def test_datapedia(self):
        self.client.get('/')

    def test_about(self):
        self.client.get('/about')

    def test_current(self):
        self.client.get('/current')

        data = {'data': 25}

        # should fail, no entries yet
        response = self.client.post('/current/foo.json', data = data)
        self.assertEquals(response.status_code, 405)
         
        # submit a new entry
        response = self.client.put('/current/foo.json', data = data)
        self.assertEquals(response.status_code, 200)

        # fetch the submited entry
        json_data = json.loads(response.data)

        self.assertBiggerOrEquals(json_data['time'], time())
        self.assertIn('127.0.0.1', json_data['approvers'])
        self.assertEquals('127.0.0.1', json_data['ip'])
        self.assertEquals(json.loads(response.data)['data'], data)

        # fetch the submitted data again
        response = self.client.get('/current/foo.json')
        self.assertEquals(json.loads(response.data), json_data)

        # submit an invalid revision of this data


        # submit a valid revision of this data

    def test_approving(self):
        self.client.get('/current')
        pass

    def test_approvings(self):
        pass

    def test_archive(self):
        pass

    def test_archives(self):
        pass

if __name__ == '__main__':
    unittest.main()
