from ..models import Receipe, Step
from flask_wtf import Form
from wtforms import StringField, DecimalField, SubmitField, SelectField, \
    IntegerField, TextAreaField, HiddenField
from wtforms.validators import Length, DataRequired, NumberRange


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


class StepForm(Form):
    # insert a hidden field with the form name for identification in multiform page
    StepForm = HiddenField("StepForm")

    # name of the step
    name = StringField(
        'Name:', validators=[DataRequired(), Length(0, Step.name.type.length)])

    # temperature setpoint in °C
    setpoint = DecimalField(
        'Temperatur:', places=0, validators=[DataRequired(),
                                            NumberRange(0, 100)]
    )

    # step duration in minutes
    duration = IntegerField(
        'Dauer:', validators=[DataRequired(),
                              NumberRange(1, 500)]
    )

    # comment
    comment = TextAreaField(
        'Kommentar:'
    )

    # submit button
    submit = SubmitField('OK')
