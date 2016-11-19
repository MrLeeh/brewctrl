import os
import blinker
import datetime
from sqlalchemy.exc import OperationalError

from . import db, socketio
from .hardware import TempController, Mixer, simulation_mode
from .models import ProcessData, init_db, Recipe


# blinker signal for new processdata
new_processdata = blinker.signal('new processdata')


class BrewControllerException(Exception):
    """ Exception occurred during brew control handling """
    pass


def background_thread(brewcontroller):

    refresh_time = brewcontroller._app.config['REFRESH_TIME']
    temperature_controller = brewcontroller.temperature_controller
    mixer = brewcontroller.mixer

    while 1:
        # sleep for the given refresh time
        socketio.sleep(refresh_time)

        # read current time
        actual_time = datetime.datetime.now()

        with brewcontroller._app.app_context():

            temperature_controller.process(actual_time)

            process_data = ProcessData()
            process_data.datetime = actual_time
            process_data.temp_setpoint = temperature_controller.setpoint
            process_data.temp_actual = temperature_controller.temp
            process_data.tempctrl_active = temperature_controller.active
            process_data.tempctrl_power = temperature_controller.power
            process_data.tempctrl_output = temperature_controller.output
            process_data.heater_enabled = temperature_controller.heater_enabled
            process_data.mixer_enabled = mixer.enabled

            # save to database
            db.session.add(process_data)
            db.session.commit()

            brewcontroller.process_data = process_data
            socketio.emit('process_data', process_data.jsonify())


class BrewController:

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._app = app
        self._logger = self._app.logger
        self._loaded_recipe_id = -1

        self.temperature_controller = TempController()
        self.mixer = Mixer()
        self.running = False
        self.loaded_recipe = None
        self.process_data = None

        try:
            with self._app.app_context():

                init_db()
                # init the temperature controller
                self.temperature_controller.load_settings()

                # clear unsaved process_data
                for p in ProcessData.query.filter(ProcessData.brewjob == None).all():
                    db.session.delete(p)
                db.session.commit()

                # init background thread
                socketio.start_background_task(background_thread, self)

        except OperationalError as e:

            self._logger.warning(str(e))

    def load_recipe(self, recipe_id):
        if self.running:
            raise BrewControllerException(
                'Can not load recipe. Another recipe is currently beeing '
                'progressed.'
            )

        with self._app.app_context():
            self.loaded_recipe = Recipe.query.get(recipe_id)
            if self.loaded_recipe is None:
                raise BrewControllerException(
                    'There is no recipe with id {}.'.format(recipe_id)
                )

        self._loaded_recipe_id = recipe_id

    def start(self):
        if self.running:
            raise BrewControllerException('Recipe already in progress.')
        else:
            self.running = True

    def shutdown(self):
        self._logger.debug('system is shutting down')
        if not simulation_mode:
            os.system('shutdown halt')
