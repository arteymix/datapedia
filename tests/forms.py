from unittest import TestCase
from wtforms import ValidationError

from src.forms import NotRegressive, JSONTextAreaField

class FormTest(TestCase):
    def test_NotRegressive(self):
        ref = {}

        # non-regressive to itself
        NotRegressive._not_regressive(ref, ref)

        # add new key
        NotRegressive._not_regressive(ref, {'foo': 1})
        
        # change root type
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, [])
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, '')

        # add another level
        ref['foo'] = {}

        # add new key
        NotRegressive._not_regressive(ref, {'bar': 1, 'foo': {}})
        NotRegressive._not_regressive(ref, {'foo': {'bar': 1}})

        # remove an existing key
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, {})

        # change root type
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, [])
       
        # change type
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, {'foo': 4})
 
        # add an empty array
        ref['bar'] = []

        NotRegressive._not_regressive(ref, ref)

        # add elements in the array
        NotRegressive._not_regressive(ref, {'foo': {}, 'bar': [1, 2, 3]})

        # add some elements
        ref['bar'] = [1, 'b', 3.3]

        # add a new element
        NotRegressive._not_regressive(ref, {'foo': {}, 'bar': [1, 'b', 3.3, 2]})

        # change elements in the array
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, {'foo': {}, 'bar': [1, 'b', 3]})

        # remove elements in the array
        self.assertRaises(ValidationError, NotRegressive._not_regressive, ref, {'foo': {}, 'bar': [1]})
  
        ref = ''

        NotRegressive._not_regressive(ref, ref)

        NotRegressive._not_regressive(ref, 'dasdasd')

    def test_JSONTextAreaField(self):
        pass
