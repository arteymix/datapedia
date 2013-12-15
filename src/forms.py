from flask_wtf import Form
from wtforms import TextField, StringField, FieldList, HiddenField, TextAreaField, SelectField, SubmitField, ValidationError
from wtforms.validators import Required, IPAddress, URL, AnyOf, EqualTo
from datapedia import SUPPORTED_EXT
import json

class JSONRequired():
    def __call__(self, form, field):
        return field.data is not None

class JSONTextAreaField(TextAreaField):
    def _value(self):
        return json.dumps(self.object_data)

    def process_formdata(self, valuelist):
        super(TextAreaField, self).process_formdata(valuelist)
        try:
            self.object_data = json.loads(self.data)
        except ValueError as ve: # json could not be parsed
            self.object_data = None
            raise ve

class NotRegressive(object):
    def __init__(self, reference):
        self.reference = reference

    def _not_regressive(self, reference, data):
        """Makes recursion cleaner"""
        if reference is None:
            return

        if type(reference) is not type(data):
            raise ValidationError(u'type {} of {} changed to {} of {}.'.format(type(reference), reference, type(data), data))

        # look further for known iterable
        if type(reference) in {list, dict, set}:
            for key in self.reference:
                if key in data:
                    self._not_regressive(reference[key], data[key])
                else:
                    raise ValidationError(u'{} is missing in {}.'.format(key, data))

    def __call__(self, form, field):
        self._not_regressive(self.reference, field.object_data)

not_regressive = NotRegressive

class RawForm(Form):
    license = SelectField('license', choices =  [
        ('CC BY', 'Attribution'), 
        ('CC BY-SA', 'Attribution-ShareAlike'),
        ('CC BY-ND', 'Attribution-NoDerivs'),
        ('CC BY-NC', 'Attribution-NonCommercial'),
        ('CC BY-NC-SA', 'Attribution-NonCommercial-ShareAlike'),
        ('CC BY-NC-ND', 'Attribution-NonCommercial-NoDerivs')
    ])
    sources = FieldList(TextField('sources', [URL()]), min_entries = 1)
    data = JSONTextAreaField('data', [JSONRequired()])

class DataForm(RawForm):
    ext = SelectField('ext', choices = [(ext, ext) for ext in SUPPORTED_EXT])
    submit = SubmitField('submit')
