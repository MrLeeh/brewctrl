import json
from itertools import islice

from . import main
from flask import request, render_template, redirect, url_for, jsonify, \
    current_app
from .forms import MainForm, ReceipeForm, TempCtrlSettingsForm, StepForm
from .. import socketio, db
from ..control import new_processdata, tempcontroller, mixer, shutdown
from ..models import ProcessData, Receipe, Step, TempCtrlSettings


def handle_new_processdata(pd):
    global actual_processdata
    actual_processdata = pd
    socketio.emit('process_data', pd)


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

    # get datapoints
    datapoint_query = ProcessData.query.filter(ProcessData.brewjob is None)
    graph_data = dict(
        time=[],
        temp=[],
        temp_setpoint=[],
        power=[]
    )

    # if datapoints more then only a point each minute
    datapoint_count = datapoint_query.count()
    datapoint_iterator = iter(datapoint_query)
    current_app.logger.debug('current datapoint count: {}'.format(datapoint_count))
    if datapoint_count > 3600:
        datapoint_iterator = islice(datapoint_iterator, 0, None, 60)

    for p in datapoint_iterator:
        graph_data['time'].append(str(p.datetime))
        graph_data['temp'].append(p.temp_actual)
        graph_data['temp_setpoint'].append(p.temp_setpoint)
        graph_data['power'].append(p.tempctrl_power)

    # is there a current receipe?
    current_receipe_id = request.cookies.get('current_receipe_id')
    if current_receipe_id is None:
        current_receipe = None
    else:
        current_receipe = Receipe.query.get(current_receipe_id)

    return render_template(
        'index.html', form=form, processdata=actual_processdata,
        graph_data=graph_data, current_receipe=current_receipe
    )


@main.route('/receipes/create', methods=['GET', 'POST'])
def create_receipe():
    form = ReceipeForm()
    receipe = Receipe()

    if form.validate_on_submit():
        receipe.name = form.name.data
        db.session.add(receipe)
        db.session.commit()

        return redirect(url_for('main.index'))

    return render_template('receipes/add.html', form=form,
                           receipe=receipe,
                           processdata=actual_processdata)


@main.route('/receipes/<receipe_id>', methods=['GET', 'POST'])
def edit_receipe(receipe_id):

    receipe = Receipe.query.filter(Receipe.id == receipe_id).first_or_404()
    form = ReceipeForm(obj=receipe)

    if form.validate_on_submit():
        receipe.name = form.name.data
        db.session.add(receipe)
        db.session.commit()
        return redirect(url_for('main.index'))

    return render_template('receipes/edit.html', form=form,
                           receipe=receipe,
                           processdata=actual_processdata)


@main.route('/receipes/<receipe_id>/steps/create', methods=['GET', 'POST'])
def create_step(receipe_id):
    receipe = Receipe.query.filter(Receipe.id == receipe_id).first_or_404()
    form = StepForm()

    # add template choices
    form.template.choices = [(x.id, x.name)
                             for x in Step.query.filter(Step.template)]
    form.template.choices.insert(0, (-1, '-'))

    if form.validate_on_submit():
        step = Step()
        step.receipe = receipe
        step.name = form.name.data
        step.setpoint = int(form.setpoint.data)
        step.duration = int(form.duration.data)
        step.comment = form.comment.data
        db.session.add(step)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('steps/add.html', form=form)


@main.route('/steps/<step_id>', methods=['GET', 'POST'])
def edit_step(step_id):
    step = Step.query.filter(Step.id == step_id).first_or_404()
    form = StepForm(obj=step)

    # add template choices
    form.template.choices = [(x.id, x.name)
                             for x in Step.query.filter(Step.template)]
    form.template.choices.insert(0, (-1, '-'))

    if form.validate_on_submit():
        step.name = form.name.data
        step.setpoint = int(form.setpoint.data)
        step.duration = int(form.duration.data)
        step.comment = form.comment.data
        db.session.add(step)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('steps/edit.html', form=form, step_id=step.id)


@main.route('/steps/<step_id>/delete', methods=['DELETE'])
def delete_step(step_id):
    step = Step.query.filter(Step.id == step_id).first()
    if step is None:
        return jsonify(
            status='error', message='no step with id {}'.format(step_id))
    db.session.delete(step)
    db.session.commit()
    return jsonify(status='ok')


@main.route('/settings/tempcontroller.html', methods=['GET', 'POST'])
def tempcontroller_settings():
    settings = TempCtrlSettings.query.first_or_404()
    form = TempCtrlSettingsForm(obj=settings)
    if form.validate_on_submit():
        settings.kp = float(form.kp.data)
        settings.tn = float(form.tn.data)
        settings.duty_cycle = float(form.duty_cycle.data)
        db.session.add(settings)
        db.session.commit()
        tempcontroller.load_settings()
        return redirect(url_for('main.index'))
    return render_template('settings/tempcontroller.html', form=form,
                           processdata=actual_processdata)


@main.route('/receipes/_list')
def ajax_list_receipes():
    receipes = Receipe.query.all()
    receipe_list = []
    for receipe in receipes:
        receipe_list.append(dict(id=receipe.id, name=receipe.name))
    return json.dumps(receipe_list)


@main.route('/receipes/load/<receipe_id>')
def load_receipe(receipe_id):
    receipe = Receipe.query.filter_by(id=receipe_id).first()
    if receipe is None:
        current_receipe_id = -1
    else:
        current_receipe_id = receipe_id
    response = current_app.make_response(redirect(url_for('main.index')))
    response.set_cookie('current_receipe_id', value=current_receipe_id)
    return response


@main.route('/receipes/_add_step', methods=['POST'])
def ajax_add_step():
    receipe_id = int(request.form['receipe_id'])
    receipe = Receipe.query.filter_by(id=receipe_id).first()
    if receipe is None:
        return '{"status": "error"}'

    step = Step()
    step.receipe = receipe
    step.name = request.form['name']
    step.setpoint = request.form['setpoint']
    step.duration = request.form['duration']
    step.comment = request.form['comment']
    step.enable_mixer = request.form['enable_mixer']

    db.session.add(step)
    db.session.commit()
    current_app.logger.debug('added step')
    return json.dumps('{"status": "ok"}')


@main.route('/steps/_templates/<step_id>', methods=['GET'])
def ajax_get_step_data(step_id):
    step = Step.query.filter_by(id=step_id).first()
    if step is None:
        return
    return jsonify(dict(
        id=step.id,
        name=step.name,
        setpoint=step.setpoint,
        duration=step.duration,
        comment=step.comment
    ))


@main.route('/steps/add', methods=['GET', 'POST'])
def add_step(receipe_id):
    pass


@socketio.on('enable_tempctrl')
def handle_enable_tempctrl(json):
    enabled = json['data']
    tempcontroller.enabled = enabled


@socketio.on('enable_mixer')
def handle_enable_mixer(json):
    enabled = json['data']
    mixer.enabled = enabled


@socketio.on('shutdown')
def handle_shutdown():
    shutdown()
