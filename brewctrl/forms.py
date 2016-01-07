"""
forms.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

from wtforms import Form, DecimalField, TextField
from wtforms.validators import required


class TempForm(Form):
    cur_temp = DecimalField("Temperatur:", places=1)
    cur_sp = DecimalField("Sollwert:", places=1)
    cur_state = TextField("Status:")
