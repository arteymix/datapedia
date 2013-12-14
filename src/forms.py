from wtforms import Form, TextField, StringField
from wtforms.validators import Required, IPAddress
import wtforms.validators
import json

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
                    return non_regressive_JSON(form, reference[key])(field[key])
                else: # a key is missing in the new data
                    raise ValidationError('{} is missing in the field {}.'.format(key, field))

        except TypeError: # if type has changed or structure is not iterable
            if type(reference) is not type(form):
                raise ValidationError('{} type has changed, it was {}.'.format(reference, form))
      
    return _non_regressive

class DataForm(Form):
    ip = Field('ip', [Required(), IPAddress()])
    license = TextField('license', [Required()])
    data = TextField('data', [Required(), NonRegressive()])
    sources = Field('sources[]', [Required()])
