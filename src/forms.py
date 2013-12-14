from flask_wtf import Form
from wtforms import TextField, StringField, FieldList, HiddenField, TextAreaField, SelectField, SubmitField, ValidationError
from wtforms.validators import Required, IPAddress, URL, AnyOf, EqualTo
from datapedia import find_data
from json import loads, dumps

def json():
    """Creates a callback to validate a JSON field"""
    def _json(form, field): 
        try:
            dumps(field.data)
        except ValueError as ve:
            raise ValidationError(ve)

    return _json

def non_regressive(reference):
    """
    Creates a callback that ensure that any given Python object is backward-compatible to the reference
    reference -- a Python object used as a reference
    """
    def _non_regressive(form, field):
        if reference is None:
            return # None is always backward-compatible

        try:
            for key in reference: # throw a TypeError if not iterable
                if key in field: # throw a TypeError if not iterable
                    return _non_regressive(form, reference[key])(field[key])
                else: # a key is missing in the new data
                    raise ValidationError('{} is missing in the field {}.'.format(key, field))

        except TypeError: # if type has changed or structure is not iterable
            if type(reference) is not type(form):
                raise ValidationError('{} type has changed, it was {}.'.format(reference, form))
      
    return _non_regressive

class RawForm(Form):
    ip = HiddenField('ip', [Required(), IPAddress()])
    license = SelectField('license', choices =  [
        ('CC BY', 'Attribution'), 
        ('CC BY-SA', 'Attribution-ShareAlike'),
        ('CC BY-ND', 'Attribution-NoDerivs'),
        ('CC BY-NC', 'Attribution-NonCommercial'),
        ('CC BY-NC-SA', 'Attribution-NonCommercial-ShareAlike'),
        ('CC BY-NC-ND', 'Attribution-NonCommercial-NoDerivs')
    ])
    sources = FieldList(TextField('sources', [URL()]), min_entries = 1)

class DataForm(RawForm):
    ext = SelectField('ext', choices = [
        ('json', 'JSON'), 
        ('xml', 'XML'),
        ('yml', 'YAML')
    ])
    data = TextAreaField('data', [Required(), json()])
    submit = SubmitField('submit')
