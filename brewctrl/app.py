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
from flask_socketio import SocketIO, emit

# monkey patching for usage of background threads
import eventlet
eventlet.monkey_patch()

from .control import read_temp
from .forms import TempForm


class Pages(Enum):
    HOME = 1
    TEMPERATURE = 2


# refresh time in seconds
ASYNC_MODE = 'eventlet'
REFRESH_TIME = 1
current_page = Pages.HOME
thread = None
cur_sp = 20
cur_heating = False
cur_state = "Heizung aus"

# temperature data buffer
temp_data = dict(x=[], y=[], type='scatter', name='Temperatur °C')
sp_data = dict(x=[], y=[], type='scatter', name='Sollwert    °C')

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
app.config['SECRET_KEY'] = 'my secret key'
socketio = SocketIO(app)


def background_thread():
    global current_page
    global cur_sp, cur_heating, cur_state
    global temp_data, sp_data

    while True:
        time.sleep(REFRESH_TIME)
        # current values
        cur_time = str(datetime.now())
        cur_temp = read_temp()

        # current state
        cur_heating = cur_temp < cur_sp
        cur_state = "Heizung ein" if cur_heating else "Heizung aus"

        # save temp data
        temp_data['x'].append(cur_time)
        temp_data['y'].append(cur_temp)

        # save setpoint data
        sp_data['x'].append(cur_time)
        sp_data['y'].append(cur_sp)

        if current_page == Pages.TEMPERATURE:
            socketio.emit(
                'pd_temp',
                {
                    'time': cur_time,
                    'temp': cur_temp,
                    'sp': cur_sp,
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
        cur_sp = float(form.cur_sp.data)

    form.cur_sp.data = cur_sp
    form.cur_state.data = cur_state
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
    graph_json = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'temp.html', form=form, ids=ids, graphJSON=graph_json
    )
