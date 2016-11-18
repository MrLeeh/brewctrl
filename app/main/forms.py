from ..models import Recipe, Step
from flask_wtf import Form
from wtforms import StringField, DecimalField, SubmitField, SelectField, \
    IntegerField, TextAreaField, BooleanField
from wtforms.validators import Length, DataRequired, NumberRange


class MainForm(Form):
    setpoint = DecimalField("Sollwert:", places=1)


class RecipeForm(Form):
    name = StringField('Rezeptname:',
                       validators=[DataRequired(),
                                   Length(1, Recipe.name.type.length)])
    comment = TextAreaField('Kommentar:', render_kw={'rows': 10})
    submit = SubmitField('OK')
    delete = SubmitField('Entfernen')


class TempCtrlSettingsForm(Form):
    kp = DecimalField("KP:", places=1)
    tn = DecimalField("TN:", places=0)
    duty_cycle = DecimalField("Duty Cycle:", places=0)
    submit = SubmitField('OK')


class StepForm(Form):
    # name of the step
    name = StringField(
        'Name:', validators=[DataRequired(), Length(0, Step.name.type.length)])

    template = SelectField('Vorlage:', coerce=int)

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

    # confirm to continue
    confirm_to_continue = BooleanField(
        'Zum Fortfahren bestätigen'
    )

    # comment
    comment = TextAreaField(
        'Kommentar:'
    )

    # submit button
    submit = SubmitField('OK')
