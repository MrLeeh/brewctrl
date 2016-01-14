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
from flask import Flask, render_template, request, url_for, redirect, abort, \
    jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from .control import TempController, set_heater_output
from .forms import TempForm, EditForm
from .models import Base, Step

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


def create_steps_graph(steps):
    total_time = 0
    x, y = [], []
    for step in steps:
        x.append(total_time)
        y.append(step.temp)
        total_time += (step.timer)
        x.append(total_time)
        y.append(step.temp)

    x.append(total_time)
    y.append(step.temp)

    return x, y


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


app = Flask(__name__)
app.config.from_object('brewctrl.config')
db = SQLAlchemy(app)
db.Model = Base
socketio = SocketIO(app)


if thread is None:
    thread = Thread(target=background_thread)
    thread.daemon = True
    thread.start()


@app.route('/')
@app.route('/index')
def index():
    steps = db.session.query(Step).order_by(Step.order).all()
    x, y = create_steps_graph(steps)

    graph = dict(
        data=[
            dict(x=x, y=y, mode='lines', name='Sollwert [°C]')
        ],
        layout=dict(
            title="Temperaturverlauf",
            height=250,
            margin=dict(
                l=40,
                r=40,
                b=40,
                t=40,
                pad=0
            ),
            xaxis=dict(
                title="Zeit [min]"
            ),
            yaxis=dict(
                title='Temperatur [°C]'
            )
        )
    )
    graph_json = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', steps=steps, graphJSON=graph_json)


@app.route('/temp', methods=['GET', 'POST'])
def handle_temp():
    global current_page
    global cur_sp

    form = TempForm(request.form)
    current_page = Pages.TEMPERATURE

    if request.method == 'POST' and form.validate():
        temp_ctrl.sp = float(form.cur_sp.data)

    form.cur_sp.data = temp_ctrl.sp
    form.cur_state.data = cur_state
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
    graph_json = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'temp.html', form=form, ids=ids, graphJSON=graph_json
    )


@app.route('/steps/create/', methods=['GET', 'POST'])
def add_step():
    step = Step()
    db.session.add(step)

    form = EditForm(request.form, step)

    if request.method == 'POST' and form.validate():
        form.populate_obj(step)
        step.order = len(db.session.query(Step).all()) - 1
        print(step.order)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', form=form)


@app.route('/steps/<int:step_id>/edit/', methods=['GET', 'POST'])
def edit_step(step_id):
    step = db.session.query(Step).get(step_id)
    if step is None:
        abort(404)

    form = EditForm(request.form, step)

    if request.method == 'POST' and form.validate():
        form.populate_obj(step)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', form=form)


@app.route('/steps/<int:step_id>/delete/', methods=['DELETE'])
def delete_step(step_id):
    step = db.session.query(Step).get(step_id)
    if step is None:
        response = jsonify({'status': 'Not found'})
        response.status = 404
        return response
    db.session.delete(step)
    db.session.commit()
    return jsonify({'status': 'OK'})


@socketio.on('step_moved', namespace='/brewctrl')
def step_moved(data):
    steps = db.session.query(Step).order_by(Step.order).all()

    # source step
    src = data['src']
    src_step = next(filter(lambda x: x.order == src, steps))

    # destination step
    dst = data['dst']
    dst_step = next(filter(lambda x: x.order == dst, steps))

    steps.remove(src_step)
    steps.insert(
        steps.index(dst_step)
        if src > dst else steps.index(dst_step) + 1, src_step
    )

    for i, step in enumerate(steps):
        step.order = i

    db.session.commit()

    x, y = create_steps_graph(steps)
    socketio.emit(
        'steps',
        {
            'time': x,
            'sp': y,
        },
        namespace='/brewctrl'
    )
