from time import time
from distutils.version import StrictVersion
from distutils.versionpredicate import VersionPredicate
from werkzeug.routing import BaseConverter, IntegerConverter, UnicodeConverter

from config import Config 
from utilities import Extension

class ExtensionConverter(UnicodeConverter):
    """Extension converter to match supported extensions in the uri."""
    def __init__(self, url_map):
        """
        extensions -- a list of supported extensions by this route
        """
        super(ExtensionConverter, self).__init__(url_map, 3, None, None)
        self.regex = '|'.join(Config.EXTENSIONS.keys())

    def to_python(self, value):
        """Returns an instance of an Extension object from the configuration."""
        return Config.EXTENSIONS[value]

class NameConverter(UnicodeConverter):
    """Defines rules for name used in Datapedia."""
    def __init__(self, url_map):
        super(NameConverter, self).__init__(url_map)
        self.regex = r'[\w\d-]+' # regex for slug

class VersionConverter(BaseConverter):
    """
    Convert and match version using StrictVersion.version_re as a regular 
    expression and VersionPredicate as a comparison from distutils.
    """
    def __init__(self, url_map, predicate):
        """
        urlmap    -- required for the BaseConverter
        predicate -- version predicate matching the parameter using 
        VersionPredicate from distutils.
        """
        super(VersionConverter, self).__init__(url_map)
        self.predicate = VersionPredicate('{} ({})'.format('foo.bar', predicate))
        self.regex = r'(\d+)\.(\d+)(\.(\d+))?([ab](\d+))?'

    def to_python(self, value):
        value = StrictVersion(value)

        if self.predicate.satisfied_by(value):
            return value

        raise ValidationError()


class TimestampConverter(IntegerConverter):
    """Timestamps are positives integers upperbounded by the current time."""
    def to_python(self, value):
        value = super(TimestampConverter, self).to_python(value)

        if not since <= value <= int(time()):
            raise ValidationError()

        return value
