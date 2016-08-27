from . import main
from flask import request, render_template
from .forms import MainForm
from ..control import new_processdata, tempcontroller

actual_processdata = None

def handle_new_processdata(pd):
    global actual_processdata
    actual_processdata = pd


new_processdata.connect(handle_new_processdata)


@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    form = MainForm()
    if form.validate_on_submit():
        tempcontroller.setpoint = float(form.setpoint.data)
    else:
        form.setpoint.data = tempcontroller.setpoint

    return render_template(
        'index.html', form=form, processdata=actual_processdata, graph_data=''
    )

    # form = MainForm(request.form)
    # if form.validate_on_submit():
    #     tempctrl.setpoint = float(form.setpoint.data)
    # else:
    #     form.setpoint.data = tempctrl.setpoint
    #
    # steps = sequence.steps
    # if len(steps) == 0:
    #     steps = get_steps()
    #
    # return render_template(
    #     'home/home.html', form=form, processdata=get_processdata(),
    #     graph_data=data, steps=steps
    pass

