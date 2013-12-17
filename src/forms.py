from flask_wtf import Form
from wtforms import TextField, StringField, FieldList, HiddenField, TextAreaField, SelectField, SubmitField, ValidationError
from wtforms.validators import Required, IPAddress, URL, AnyOf, EqualTo
import datapedia
import json
from config import Config as config

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

    @staticmethod
    def _not_regressive(reference, data):
        """Makes recursion cleaner"""
        if reference is None:
            return

        if type(reference) is not type(data):
            raise ValidationError(u'type {} of {} changed to {} of {}.'.format(type(reference), reference, type(data), data))

        # look further for known iterable
        if type(reference) == dict:
            for key in reference:
                if key in data:
                    NotRegressive._not_regressive(reference[key], data[key])
                else:
                    raise ValidationError(u'key {} is missing in {}.'.format(key, data))

        if type(reference) == list:
            for index, value in enumerate(reference):
                if index >= len(data):
                    raise ValidationError(u'index {} is missing in {}.'.format(index, data))

                NotRegressive._not_regressive(reference[index], data[index])

    def __call__(self, form, field):
        self._not_regressive(self.reference, field.object_data)

not_regressive = NotRegressive

class CurrentForm(Form):
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
    ext = SelectField('ext', choices = [(ext, ext) for ext in config.SUPPORTED_EXT])
    submit = SubmitField('Submit')

class ApprovingForm(Form):
    """Form for approving a data"""
    ext = HiddenField('ext', default = config.SUPPORTED_EXT[0])
    submit = SubmitField('Approve')
