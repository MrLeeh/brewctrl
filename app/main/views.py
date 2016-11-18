import json
from itertools import islice

from . import main
from flask import request, render_template, redirect, url_for, jsonify, \
    current_app
from .forms import MainForm, RecipeForm, TempCtrlSettingsForm, StepForm
from .. import socketio, db, brew_controller
from ..brewcontroller import new_processdata
from ..models import ProcessData, Recipe, Step, TempCtrlSettings


def handle_new_processdata(pd):
    global actual_processdata
    actual_processdata = pd
    socketio.emit('process_data', pd)


new_processdata.connect(handle_new_processdata)
actual_processdata = None
current_recipe_id = -1


@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    form = MainForm()

    temperature_controller = brew_controller.temperature_controller
    if form.validate_on_submit():
        temperature_controller.setpoint = float(form.setpoint.data)
    else:
        form.setpoint.data = temperature_controller.setpoint

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
    current_app.logger.debug(
        'current datapoint count: {}'.format(datapoint_count))
    if datapoint_count > 3600:
        datapoint_iterator = islice(datapoint_iterator, 0, None, 60)

    for p in datapoint_iterator:
        graph_data['time'].append(str(p.datetime))
        graph_data['temp'].append(p.temp_actual)
        graph_data['temp_setpoint'].append(p.temp_setpoint)
        graph_data['power'].append(p.tempctrl_power)

    # is there a current recipe?
    global current_recipe_id
    if current_recipe_id is None:
        current_recipe = None
    else:
        current_recipe = Recipe.query.get(current_recipe_id)

    return render_template(
        'index.html', form=form, processdata=actual_processdata,
        graph_data=graph_data, current_recipe=current_recipe
    )


@main.route('/recipes/create')
def create_recipe():
    recipe = Recipe()
    recipe.name = request.args['name'] or 'Neues Rezept'
    db.session.add(recipe)
    db.session.commit()

    return redirect(url_for('.edit_recipe', recipe_id=recipe.id))


@main.route('/recipes/<recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    recipe = Recipe.query.filter(Recipe.id == recipe_id).first_or_404()
    form = RecipeForm(obj=recipe)

    if 'delete' in request.args:
        db.session.delete(recipe)
        db.session.commit()
        return redirect(url_for('main.index'))

    if form.validate_on_submit():
        recipe.name = form.name.data
        db.session.add(recipe)
        db.session.commit()
        return redirect(url_for('main.index'))

    return render_template('recipes/edit.html', form=form,
                           recipe=recipe, processdata=actual_processdata)


@main.route('/recipes/<recipe_id>/steps/create', methods=['GET', 'POST'])
def create_step(recipe_id):
    form = StepForm()

    # add template choices
    form.template.choices = [(x.id, x.name)
                             for x in Step.query.filter(Step.template)]
    form.template.choices.insert(0, (-1, '-'))

    if form.validate_on_submit():
        step = Step()
        step.recipe_id = recipe_id
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
        step.confirm_to_continue = bool(form.confirm_to_continue.data)
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


@main.route('/settings/temperature_controller.html', methods=['GET', 'POST'])
def tempcontroller_settings():
    settings = TempCtrlSettings.query.first_or_404()
    form = TempCtrlSettingsForm(obj=settings)
    if form.validate_on_submit():
        settings.kp = float(form.kp.data)
        settings.tn = float(form.tn.data)
        settings.duty_cycle = float(form.duty_cycle.data)
        db.session.add(settings)
        db.session.commit()
        brew_controller.temperature_controller.load_settings()
        return redirect(url_for('main.index'))
    return render_template('settings/tempcontroller.html', form=form,
                           processdata=actual_processdata)


@main.route('/recipes/_list')
def ajax_list_recipes():
    recipes = Recipe.query.all()
    recipe_list = []
    for recipe in recipes:
        recipe_list.append(dict(id=recipe.id, name=recipe.name))
    return json.dumps(recipe_list)


@main.route('/recipes/load/<recipe_id>')
def load_recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    global current_recipe_id
    if recipe is None:
        current_recipe_id = -1
    else:
        current_recipe_id = recipe_id

    return redirect(url_for('main.index'))


@main.route('/recipes/_add_step', methods=['POST'])
def ajax_add_step():
    recipe_id = int(request.form['recipe_id'])
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    if recipe is None:
        return '{"status": "error"}'

    step = Step()
    step.recipe = recipe
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
def add_step():
    pass


@socketio.on('enable_tempctrl')
def handle_enable_tempctrl(json_):
    enabled = json_['data']
    brew_controller.temperature_controller.enabled = enabled


@socketio.on('enable_mixer')
def handle_enable_mixer(json_):
    enabled = json_['data']
    brew_controller.mixer.enabled = enabled


@socketio.on('shutdown')
def handle_shutdown():
    brew_controller.shutdown()
