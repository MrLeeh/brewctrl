"""
app.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

import json
from datetime import datetime
from threading import Timer

import plotly
from flask import Flask, render_template, request, url_for, redirect, abort, \
    jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from .config import REFRESH_TIME, NAMESPACE
from .control import TempController
from .forms import TempForm, EditForm
from .models import Base, Step, ProcessData
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

# temperature controller
temp_ctrl = TempController()
# sequence controller
sequence = Sequence()
recording_enabled = False


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


def create_processdata_graph():
    # temperature data buffer
    temp_data = dict(x=[], y=[], type='scatter', name='Temperatur [°C]')
    sp_data = dict(x=[], y=[], type='scatter', name='Sollwert [°C]')

    for data in db.session.query(ProcessData).all():
        temp_data['x'].append(str(data.timestamp))
        temp_data['y'].append(data.temp)

        sp_data['x'].append(str(data.timestamp))
        sp_data['y'].append(data.temp_setpoint)

    graphs = [
        dict(
            data=[temp_data, sp_data],
            layout=dict(
                title="Temperaturverlauf"
            )
        )
    ]
    return graphs


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
    temp_ctrl.process()

    # process sequence controller
    sequence.process(temp_ctrl.temp, cur_time)
    if sequence.running and not sequence.pause:
        temp_ctrl.sp = sequence.cur_setpoint

    # if enabled do data recording
    if recording_enabled:
        data = ProcessData()
        data.timestamp = cur_time
        data.temp_setpoint = temp_ctrl.sp
        data.temp = temp_ctrl.temp
        db.session.add(data)
        db.session.commit()

    process_data = {
        'pause': sequence.pause,
        'progress': format_td(sequence.progress),
        'recording_enabled': recording_enabled,
        'running': sequence.running,
        'temp': temp_ctrl.temp,
        'temp_setpoint': temp_ctrl.sp,
        'time': str(cur_time),
        'state': temp_ctrl.state,
    }

    if sequence.running:
        process_data['step_id'] = sequence.cur_step.id

    socketio.emit('process_data', process_data, namespace=NAMESPACE)


# init background thread
t = Timer(REFRESH_TIME, background_thread)
t.daemon = True
t.start()


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
    return render_template(
        'index.html', steps=steps, graphJSON=graph_json,
        recording_enabled=recording_enabled
    )


@app.route('/temp', methods=['GET', 'POST'])
def handle_temp():
    form = TempForm(request.form)

    if request.method == 'POST' and form.validate():
        temp_ctrl.sp = float(form.cur_sp.data)

    form.cur_sp.data = temp_ctrl.sp
    form.cur_state.data = temp_ctrl.state

    graphs = create_processdata_graph()
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
    graph_json = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'temp.html', form=form, ids=ids, graphJSON=graph_json,
        recording_enabled=recording_enabled
    )


@app.route('/steps', methods=['GET'])
def handle_steps():
    steps = db.session.query(Step).order_by(Step.order).all()
    x, y = create_steps_graph(steps)

    graph = dict(
        data=[
            dict(x=x, y=y, mode='lines', name='Sollwert [°C]')
        ],
        layout=dict(
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
            ),
            showlegend=False
        ),
        config=dict(
            staticPlot=True
        )
    )
    graph_json = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'steps.html', steps=steps, graphJSON=graph_json,
    )


@app.route('/steps/create/', methods=['GET', 'POST'])
def add_step():
    step = Step()
    db.session.add(step)

    form = EditForm(request.form, step)

    if request.method == 'POST' and form.validate():
        form.populate_obj(step)
        step.order = len(db.session.query(Step).all()) - 1
        db.session.commit()
        return redirect(url_for('handle_steps'))

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
        return redirect(url_for('handle_steps'))

    return render_template('edit.html', form=form)


@app.route('/steps/<int:step_id>/insert_before/', methods=['GET', 'POST'])
def insert_step_before(step_id):
    ref_step = db.session.query(Step).get(step_id)
    ref_order = ref_step.order
    steps = db.session.query(Step).order_by(Step.order).all()

    insert = False
    for step in steps:
        if step.id == step_id:
            insert = True
        if insert:
            step.order += 1

    new_step = Step()
    new_step.order = ref_order
    db.session.add(new_step)

    form = EditForm(request.form, new_step)

    if request.method == 'POST' and form.validate():
        form.populate_obj(new_step)
        db.session.commit()
        return redirect(url_for('handle_steps'))

    return render_template('edit.html', form=form)


@app.route('/steps/<int:step_id>/insert_after/', methods=['GET', 'POST'])
def insert_step_after(step_id):
    ref_step = db.session.query(Step).get(step_id)
    ref_order = ref_step.order
    steps = db.session.query(Step).order_by(Step.order).all()

    insert = False
    for step in steps:
        if insert:
            step.order += 1
        elif step.id == step_id:
            insert = True

    new_step = Step()
    new_step.order = ref_order + 1
    db.session.add(new_step)

    form = EditForm(request.form, new_step)

    if request.method == 'POST' and form.validate():
        form.populate_obj(new_step)
        db.session.commit()
        return redirect(url_for('handle_steps'))

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

    steps = db.session.query(Step).order_by(Step.order).all()
    for i, step in enumerate(steps):
        step.order = i
    db.session.commit()
    return jsonify({'status': 'OK'})


@socketio.on('step_moved', namespace=NAMESPACE)
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
        namespace=NAMESPACE
    )


@socketio.on('connected', namespace=NAMESPACE)
def connected(data):
    name = str(data['name'])
    print('IOSocket connection to {}'.format(name))


@socketio.on('clear_data', namespace=NAMESPACE)
def clear_data(data):
    db.session.query(ProcessData).delete()
    db.session.commit()


@socketio.on('start_recording', namespace=NAMESPACE)
def start_recording(data):
    global recording_enabled
    recording_enabled = True


@socketio.on('stop_recording', namespace=NAMESPACE)
def stop_recording(data):
    global recording_enabled
    recording_enabled = False


@socketio.on('start_sequence', namespace=NAMESPACE)
def start_sequence(data):
    if not sequence.running:
        sequence.start()
    else:
        sequence.toggle_pause()


@socketio.on('stop_sequence', namespace=NAMESPACE)
def stop_sequence(data):
    sequence.stop()
