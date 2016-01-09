"""
forms.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

from wtforms import Form, DecimalField, IntegerField, TextField, TextAreaField
from wtforms.validators import required, Length, NumberRange


class TempForm(Form):
    cur_temp = DecimalField("Temperatur:", places=1)
    cur_sp = DecimalField("Sollwert:", places=1)
    cur_state = TextField("Status:")


class EditForm(Form):
    name = TextField('Name:', [required(), Length(max=80)])
    temp = IntegerField('Temperatur:', [required(), NumberRange(20, 110)])
    timer = IntegerField('Timer:', [NumberRange(0, 120)])
    comment = TextAreaField('Kommentar:')
