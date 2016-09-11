from ..models import Receipe
from flask_wtf import Form
from wtforms import StringField, DecimalField, SubmitField, SelectField
from wtforms.validators import Length, DataRequired


class MainForm(Form):
    setpoint = DecimalField("Sollwert:", places=1)


class ReceipeForm(Form):
    name = StringField('Rezeptname:',
                       validators=[DataRequired(),
                                   Length(1, Receipe.name.type.length)])
    submit = SubmitField('OK')


class TempCtrlSettingsForm(Form):
    kp = DecimalField("KP:", places=1)
    tn = DecimalField("TN:", places=0)
    duty_cycle = DecimalField("Duty Cycle:", places=0)
    submit = SubmitField('OK')
