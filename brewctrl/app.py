"""
app.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from datetime import datetime
from threading import Timer
import json

from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask_socketio import SocketIO

from .config import REFRESH_TIME
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
# toolbar = DebugToolbarExtension(app)

from .sequence import Sequence

# Global Variables

# sequence controller
sequence = Sequence()
recording_enabled = False

# temperature controller
from .control import TempController

tempctrl_settings = db.session.query(TempCtrlSettings).first()
if tempctrl_settings is None:
    tempctrl_settings = TempCtrlSettings()
    db.session.add(tempctrl_settings)
    db.session.commit()

tempctrl = TempController()
tempctrl.load_settings()


def get_processdata():
    return {
        'temp': tempctrl.temp,
        'temp_setpoint': tempctrl.setpoint,
        'time': str(datetime.now()),
        'state': tempctrl.state,
        'active': tempctrl.active,
        'power': tempctrl.power,
        'output': tempctrl.output
    }


def background_thread():
    global url_rule, recording_enabled
    global temp_data, sp_data

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

    process_data = get_processdata()

    # if sequence.running:
    #     process_data['step_id'] = sequence.cur_step.id

    socketio.emit('process_data', process_data)


# init background thread
t = Timer(REFRESH_TIME, background_thread)
t.daemon = True
t.start()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', processdata=get_processdata())


@app.route('/tempctrl-settings', methods=['GET', 'POST'])
def tempctrl_settings():
    tempctrl_settings = db.session.query(TempCtrlSettings).first()
    form = TempForm(request.form, obj=tempctrl_settings)

    if form.validate_on_submit():
        form.populate_obj(tempctrl_settings)
        db.session.commit()

        tempctrl.load_settings()
        return redirect(url_for('tempctrl_settings'))

    return render_template('tempctrl/tempctrl.html', form=form,
                           processdata=get_processdata())


@socketio.on('enable_tempctrl')
def handle_json(json):
    enable = json['data']
    tempctrl.active = enable


@socketio.on('reset_tempctrl')
def handle_reset_tempctrl():
    tempctrl.reset = True
