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

from unittest import TestCase
from wtforms import ValidationError

from datapedia.forms import NotRegressive, JSONTextAreaField

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
