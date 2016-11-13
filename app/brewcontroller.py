import os
import blinker
import datetime
from threading import Timer
from sqlalchemy.exc import OperationalError

from . import db
from .hardware import TempController, Mixer, simulation_mode
from .models import TempCtrlSettings, ProcessData, init_db


# blinker signal for new processdata
new_processdata = blinker.signal('new processdata')


def background_thread(brewcontroller):
    actual_time = datetime.datetime.now()

    # create a new timer and call it
    t = Timer(
        brewcontroller._app.config['REFRESH_TIME'],
        background_thread, args=[brewcontroller])
    t.daemon = True
    t.start()

    temperature_controller = brewcontroller.temperature_controller
    mixer = brewcontroller.mixer
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
        db.session.add(process_data)
        db.session.commit()

        new_processdata.send(process_data.jsonify())


class BrewController:

    def __init__(self, app=None):

        pass

    def init_app(self, app):

        self._app = app
        self._logger = self._app.logger
        self.temperature_controller = TempController()
        self.mixer = Mixer()

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
                t = Timer(app.config['REFRESH_TIME'], background_thread, [self])
                t.daemon = True
                t.start()

        except OperationalError as e:
            self._app.logger.error(e)

    def shutdown(self):
        self._logger.debug('system is shutting down')
        if not simulation_mode:
            os.system('shutdown halt')
