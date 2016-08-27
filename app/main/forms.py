from flask_wtf import Form
from wtforms import DecimalField


class MainForm(Form):
    setpoint = DecimalField("Sollwert:", places=1)
