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

SIMULATION = False

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'

try:
    device_folder = glob.glob(base_dir + '10*')[0]
    device_file = device_folder + '/w1_slave'
except IndexError:
    print("No Temp.sensors found. Continue in simulation mode.")
    SIMULATION = True


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp():
    if SIMULATION:
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


class TempController:

    def __init__(self, parent=None):
        self.active = False
        self.heater_on = False
        self.sp = 20
        self._temp = 20
        self.bandwith = 1.0

    def process(self):
        self._temp = read_temp()

        if ((self.temp < self.sp + self.bandwith and self.heater_on) or
                (self.temp < self.sp - self.bandwith and not self.heater_on)):
            self.heater_on = True
        elif self.temp >= self.sp + self.bandwith:
            self.heater_on = False

    # current temperature readonly propety
    @property
    def temp(self):
        return self._temp


if __name__ == '__main__':
    print(read_temp())
