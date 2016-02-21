"""
app.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from datetime import datetime
from threading import Timer

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from .config import REFRESH_TIME, NAMESPACE
from .forms import TempForm
from .models import Base
from .models import TempCtrl as TempCtrlSettings
from .util import format_td

# monkey patching for usage of background threads
import eventlet
eventlet.monkey_patch()

# setup  flask application
app = Flask(__name__)
app.config.from_object('brewctrl.config')
db = SQLAlchemy(app)
db.Model = Base
socketio = SocketIO(app)

from .sequence import Sequence

# Global Variables

# sequence controller
sequence = Sequence()
recording_enabled = False

# temperature controller
from .control import TempController, MODE_MANUAL
session = db.session
tempctrl_settings = session.query(TempCtrlSettings).first()
if tempctrl_settings is None:
    tempctrl_settings = TempCtrlSettings()
    session.add(tempctrl_settings)
    session.commit()

tempctrl = TempController()
tempctrl.load_settings()


def background_thread():
    global url_rule, recording_enabled
    global temp_data, sp_data

    # current values
    cur_time = datetime.now()

    # restart timer
    t = Timer(REFRESH_TIME, background_thread)
    t.daemon = True
    t.start()

    # process temperature controller
    tempctrl.process()

    # # process sequence controller
    # sequence.process(tempctrl.temp, cur_time)
    # if sequence.running and not sequence.pause:
    #     tempctrl.setpoint = sequence.cur_setpoint

    # # if enabled do data recording
    # if recording_enabled:
    #     data = ProcessData()
    #     data.timestamp = cur_time
    #     data.temp_setpoint = tempctrl.setpoint
    #     data.temp = tempctrl.temp
    #     db.session.add(data)
    #     db.session.commit()

    process_data = {
        'pause': sequence.pause,
        'progress': format_td(sequence.progress),
        'recording_enabled': recording_enabled,
        'running': sequence.running,
        'temp': tempctrl.temp,
        'temp_setpoint': tempctrl.setpoint,
        'time': str(cur_time),
        'state': tempctrl.state,
        'power': tempctrl.power,
        'output': tempctrl.output
    }

    # if sequence.running:
    #     process_data['step_id'] = sequence.cur_step.id

    socketio.emit('process_data', process_data, namespace=NAMESPACE)


# init background thread
t = Timer(REFRESH_TIME, background_thread)
t.daemon = True
t.start()


@app.route('/')
@app.route('/index')
def index():
    return render_template('base.html')


@app.route('/tempctrl-settings', methods=['GET', 'POST'])
def tempctrl_settings():
    tempctrl_settings = db.session.query(TempCtrlSettings).first()
    form = TempForm(request.form, obj=tempctrl_settings)

    if form.validate_on_submit():
        form.populate_obj(tempctrl_settings)
        session.commit()

        tempctrl.load_settings()
        return redirect(url_for('tempctrl_settings'))

    return render_template('tempctrl/tempctrl.html', form=form)
