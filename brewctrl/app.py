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

from .config import REFRESH_TIME
from .forms import TempForm, MainForm

# monkey patching for usage of background threads
import eventlet
eventlet.monkey_patch()

# setup  flask application
app = Flask(__name__)
app.config.from_object('brewctrl.config')
db = SQLAlchemy(app)
socketio = SocketIO(app)

from .models import TempCtrl as TempCtrlSettings, Step


# temperature controller
from .control import TempController
tempctrl_settings = db.session.query(TempCtrlSettings).first()

if tempctrl_settings is None:
    tempctrl_settings = TempCtrlSettings()
    db.session.add(tempctrl_settings)
    db.session.commit()

tempctrl = TempController()
tempctrl.load_settings()
data = dict(
    time=[],
    temp=[],
    temp_setpoint=[],
    power=[]
)


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


def get_steps():
    return Step.query.all()


def background_thread():
    # restart timer
    t = Timer(REFRESH_TIME, background_thread)
    t.daemon = True
    t.start()

    # process temperature controller
    tempctrl.process()
    processdata = get_processdata()
    data['time'].append(processdata['time'])
    data['temp'].append(processdata['temp'])
    data['temp_setpoint'].append(processdata['temp_setpoint'])
    data['power'].append(processdata['power'])

    socketio.emit('process_data', processdata)


# init background thread
t = Timer(REFRESH_TIME, background_thread)
t.daemon = True
t.start()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = MainForm(request.form)

    if form.validate_on_submit():
        tempctrl.setpoint = float(form.setpoint.data)
    else:
        form.setpoint.data = tempctrl.setpoint

    return render_template(
        'home/home.html', form=form, processdata=get_processdata(),
        graph_data=data, steps=get_steps()
    )


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


@app.route('/steps')
def steps():
    return render_template('steps.html')


@socketio.on('enable_tempctrl')
def handle_json(json):
    enable = json['data']
    tempctrl.active = enable


@socketio.on('reset_tempctrl')
def handle_reset_tempctrl():
    tempctrl.reset = True


@socketio.on('reset_graph')
def handle_reset_graph():
    for key in data:
        data[key].clear()


@socketio.on('set_setpoint')
def handle_set_setpoint(setpoint):
    tempctrl.setpoint = setpoint
