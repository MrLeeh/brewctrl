#!/usr/bin/env python

"""
control.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
import os
import glob
import time
import random

# Hardware configuration
TEMPSENSOR = '28*'
HEATER_PIN = 24

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
        self.active = False
        self._heater_enabled = False
        self.sp = 20
        self._temp = 20
        self.bandwith = 0.1

    def process(self):
        self._temp = read_temp()

        if ((self.temp < self.sp + self.bandwith and self.heater_enabled) or
                (self.temp < self.sp - self.bandwith and not self.heater_enabled)):
            self.heater_enabled = True
        elif self.temp >= self.sp + self.bandwith:
            self.heater_enabled = False

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
