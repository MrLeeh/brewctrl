"""
forms.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

from flask_wtf import Form
from wtforms import DecimalField, IntegerField, TextField, TextAreaField, \
    SelectField
from wtforms.validators import required, Length, NumberRange


class TempForm(Form):
    setpoint = DecimalField("Sollwert:", places=1)
    temp = DecimalField("Istwert:", places=1)
    power = DecimalField("Leistung:", places=0)
    state = TextField("Status:")
    mode = SelectField("Modus:", choices=[
        ('manual', 'Steuerung'), ('auto', 'Regelung')])
    kp = DecimalField("KP:", places=1)
    tn = DecimalField("TN:", places=0)
    duty_cycle = DecimalField("Duty Cycle:", places=0)


class EditForm(Form):
    name = TextField('Name:', [required(), Length(max=80)])
    temp = IntegerField('Temperatur:', [required(), NumberRange(20, 110)])
    timer = IntegerField('Timer:', [NumberRange(0, 120)])
    comment = TextAreaField('Kommentar:')
