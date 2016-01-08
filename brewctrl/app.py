"""
app.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

import json
import time
from datetime import datetime
from threading import Thread
from enum import Enum

import plotly
from flask import Flask, render_template, request
from flask_socketio import SocketIO

from .control import TempController
from .forms import TempForm

# monkey patching for usage of background threads
import eventlet
eventlet.monkey_patch()


class Pages(Enum):
    HOME = 1
    TEMPERATURE = 2


# refresh time in seconds
ASYNC_MODE = 'eventlet'
REFRESH_TIME = 1
current_page = Pages.HOME
temp_ctrl = TempController()
thread = None
cur_state = "Heizung aus"

# temperature data buffer
temp_data = dict(x=[], y=[], type='scatter', name='Temperatur [°C]')
sp_data = dict(x=[], y=[], type='scatter', name='Sollwert [°C]')

# graph data
graphs = [
    dict(
        data=[temp_data, sp_data],
        layout=dict(
            title="Temperaturverlauf"
        )
    )
]


app = Flask(__name__)
app.config.from_object('brewctrl.config')
socketio = SocketIO(app)


def background_thread():
    global current_page
    global temp_data, sp_data

    while True:
        time.sleep(REFRESH_TIME)
        # current values
        cur_time = str(datetime.now())

        temp_ctrl.process()

        # current state
        cur_state = "Heizung ein" if temp_ctrl.heater_on else "Heizung aus"

        # save temp data
        temp_data['x'].append(cur_time)
        temp_data['y'].append(temp_ctrl.temp)

        # save setpoint data
        sp_data['x'].append(cur_time)
        sp_data['y'].append(temp_ctrl.sp)

        if current_page == Pages.TEMPERATURE:
            socketio.emit(
                'pd_temp',
                {
                    'time': cur_time,
                    'temp': temp_ctrl.temp,
                    'sp': temp_ctrl.sp,
                    'state': cur_state
                },
                namespace='/processdata'
            )


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/temp', methods=['GET', 'POST'])
def handle_temp():
    global thread
    global current_page
    global cur_sp

    form = TempForm(request.form)
    current_page = Pages.TEMPERATURE

    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()

    if request.method == 'POST' and form.validate():
        temp_ctrl.sp = float(form.cur_sp.data)

    form.cur_sp.data = temp_ctrl.sp
    form.cur_state.data = cur_state
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
    graph_json = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'temp.html', form=form, ids=ids, graphJSON=graph_json
    )
