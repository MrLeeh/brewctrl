#!/usr/bin/env python

"""
simulation.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

from datetime import datetime


class SimulationModel:

    def __init__(self):
        self.T1 = 120
        self.K = 1.0
        self.temp = 20

        self.temp_1 = self.temp
        self._prev_time = None

    def process(self, power):
        cur_time = datetime.utcnow()

        if self._prev_time is not None:
            dt = (cur_time - self._prev_time).total_seconds()
        else:
            dt = 0

        if dt == 0:
            self.temp = self.temp_1
        else:
            T_ = 1 / (self.T1 / dt + 1)
            self.temp = T_ * (self.K * power - self.temp_1) + self.temp_1
            self.temp_1 = self.temp

        self._prev_time = cur_time
        return self.temp
