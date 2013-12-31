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

class Extension(object):
    """
    Object representing an extension in url such as json or xml
    and provide dump and load utilities.
    """
    def __init__(self, extension, loads, dumps):
        """
        extension -- str      is the name of the extension.
        loads     -- function a callback for loading data from that format.
        dumps     -- function a callback for dumping data in that format.
        """
        self.extension = extension
        self.loads = loads
        self.dumps = dumps

    def dump(self, obj, f):
        f.write(self.dumps(obj))

    def load(self, f):
        return self.loads(f.read())

    def __str__(self):
        return self.extension
