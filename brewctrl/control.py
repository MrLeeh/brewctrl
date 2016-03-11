#!/usr/bin/env python

"""
control.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
import os
import logging
import glob
from datetime import datetime
import time
import random

from .app import db
from .models import TempCtrl

# Hardware configuration
TEMPSENSOR = '28*'
HEATER_PIN = 24

MODE_AUTO = 'auto'
MODE_MANUAL = 'manual'
MAX = 100
MIN = 0


logger = logging.getLogger('brewctrl.control')
simulation_mode = False

# enable gpio and onewire functions
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
os.system('gpio export {pin} out'.format(pin=HEATER_PIN))

base_dir = '/sys/bus/w1/devices/'
try:
    device_folder = glob.glob(base_dir + TEMPSENSOR)[0]
    device_file = device_folder + '/w1_slave'
except IndexError:
    print("No Temp.sensors found. Continue in simulation mode.")
    simulation_mode = True
    from .simulation import SimulationModel
    simulation_model = SimulationModel()


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp():
    if simulation_mode:
        temp_c = simulation_model.temp
        return temp_c
    else:
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c


def set_heater_output(val: bool):
    os.system('gpio -g write {pin} {state}'.format(
        pin=HEATER_PIN, state=1 if val else 0
    ))


class PWM_DC:

    def __init__(self):
        self._t0 = datetime.utcnow()
        self.in_pct = 0.0
        self.duty_cycle = 60.0
        self.out = False

    def process(self, in_pct=None):
        if in_pct is not None:
            self.in_pct = in_pct

        t = datetime.utcnow()
        dt = (t - self._t0).total_seconds()

        if dt > self.duty_cycle:
            self._t0 = t
            dt = 0

        on_time = self.in_pct / 100.0 * self.duty_cycle
        self.out = False if in_pct == 0 else dt <= on_time
        return self.out


class TempController:

    """ Temperature controller """

    def __init__(self, parent=None):
        self.pwm = PWM_DC()
        self._heater_enabled = False
        self._temp = 20
        self._temp_delta = 0
        self._time_delta = 0
        self._prev_time = None
        self._p = 0
        self._i = 0
        self.setpoint = 50
        self.kp = 10.0
        self.tn = 180.0
        self.duty_cycle = 60.0
        self.mode = MODE_AUTO
        self.manual_power = 50.0
        self.active = False
        self.reset = False
        self.output = False

    def process(self, cur_time=datetime.utcnow()):

        if self._prev_time is not None:
            self._time_delta = (cur_time - self._prev_time).total_seconds()
        else:
            self._time_delta = 0

        # get current temperature
        self._temp = read_temp()

        if self.active:

            if self.mode == MODE_AUTO:
                self._temp_delta = self.setpoint - self._temp

                # proportional part
                self._p = self.kp * self._temp_delta

                # integral part
                if self.reset:
                    self._i = 0
                    self.reset = False
                else:
                    if not self.tn == 0:
                        self._i += self._time_delta * self._temp_delta / self.tn
                        self._i = max(min(self._i, MAX), MIN)

                # output
                self.power = self._p + self._i

            else:
                self.power = self.manual_power

            self.power = max(min(self.power, MAX), MIN)

            # pwm duty duty_cycle
            self.output = self.pwm.process(self.power)
        else:
            self.power = 0.0
            self.output = False

        if simulation_mode:
            simulation_model.process(self.power)

        self.heater_enabled = self.output
        self._prev_time = cur_time

    def load_settings(self):
        settings = db.session.query(TempCtrl).first()
        if settings is None:
            logger.error('No settings found for temperature controller')
            return

        attributes = ['setpoint', 'kp', 'tn', 'duty_cycle', 'mode', 'manual_power']
        for attr in attributes:
            setattr(self, attr, getattr(settings, attr))

    # temperature property
    @property
    def temp(self):
        return self._temp

    # heater_enabled property
    @property
    def heater_enabled(self):
        return self._heater_enabled

    @heater_enabled.setter
    def heater_enabled(self, value: bool):
        self._heater_enabled = value
        if not simulation_mode:
            set_heater_output(value)

    # duty cycle
    @property
    def duty_cycle(self):
        return self.pwm.duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, value):
        self.pwm.duty_cycle = value

    # state
    @property
    def state(self):
        if self.heater_enabled:
            return 'Heizung ein'
        else:
            return 'Heizung aus'

if __name__ == '__main__':
    print(read_temp())
