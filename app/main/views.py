import logging

from . import main
from flask import request, render_template
from .forms import MainForm
from .. import socketio
from ..control import new_processdata, tempcontroller, mixer
from ..models import ProcessData


def handle_new_processdata(pd):
    global actual_processdata
    actual_processdata = pd
    socketio.emit('process_data', pd)


logger = logging.getLogger('brewctrl.main.views')
new_processdata.connect(handle_new_processdata)
actual_processdata = None


@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    form = MainForm()
    if form.validate_on_submit():
        tempcontroller.setpoint = float(form.setpoint.data)
    else:
        form.setpoint.data = tempcontroller.setpoint

    datapoints = ProcessData.query.filter(ProcessData.brewjob == None).all()
    graph_data = dict(
        time=[],
        temp=[],
        temp_setpoint=[],
        power=[]
    )
    for p in datapoints:
        graph_data['time'].append(str(p.datetime))
        graph_data['temp'].append(p.temp_actual)
        graph_data['temp_setpoint'].append(p.temp_setpoint)
        graph_data['power'].append(p.tempctrl_power)

    return render_template(
        'index.html', form=form, processdata=actual_processdata,
        graph_data=graph_data
    )


@socketio.on('enable_tempctrl')
def handle_enable_tempctrl(json):
   enabled = json['data']
   tempcontroller.enabled = enabled


@socketio.on('enable_mixer')
def handle_enable_mixer(json):
    enabled = json['data']
    mixer.enabled = enabled
