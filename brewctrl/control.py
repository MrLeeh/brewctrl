#!/usr/bin/env python

"""
control.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
import os
import glob
from datetime import datetime
import time
import random

# Hardware configuration
TEMPSENSOR = '28*'
HEATER_PIN = 24

MODE_AUTO = 'auto'
MODE_MANUAL = 'manual'
MAX = 100
MIN = 0

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


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp():
    if simulation_mode:
        temp_c = 20. + (random.random() * 10 - 5)
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


class TempController:

    """ Temperature controller """

    def __init__(self, parent=None):
        self._heater_enabled = False
        self._temp = 20
        self._temp_delta = 0
        self._time_delta = 0
        self._prev_time = None
        self._p = 0
        self._i = 0
        self.active = False
        self.setpoint = 20
        self.mode = MODE_AUTO
        self.kp = 10.0
        self.tn = 180.0
        self.power = 0.0
        self.reset = False
        self.duty_cycle = 60.0

    def process(self):
        cur_time = datetime.utcnow()

        if self._prev_time is not None:
            self._time_delta = (cur_time - self._prev_time).total_seconds()
        else:
            self._time_delta = 0

        # get current temperature
        self._temp = read_temp()

        self._temp_delta = self.setpoint - self._temp

        # proportional part
        self._p = self.kp * self._temp_delta

        # integral part
        if self.reset:
            self._i = 0
        else:
            self._i += self._time_delta * self._temp_delta / self.tn
            self._i = max(min(self._i, MAX), MIN)

        # output
        self.power = self._p + self._i
        self.power = max(min(self.power, MAX), MIN)

        self._prev_time = cur_time
        print(self._temp_delta, self._time_delta, self._p, self._i, self.power)

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

    @property
    def state(self):
        if self.heater_enabled:
            return 'Heizung ein'
        else:
            return 'Heizung aus'

if __name__ == '__main__':
    print(read_temp())
