"""
sequence.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from datetime import datetime, timedelta

from .app import db
from .models import Step


def td_to_min(td: timedelta):
    """ Convert Timedelta object to minutes """
    return td.seconds / 60


class Sequence:

    def __init__(self):
        self.running = False
        self.progress = timedelta()
        self.pause = False
        self.steps = []
        self._prev_time = None

        self.refresh_steplist()

    def refresh_steplist(self):
        # get list of steps
        steps = db.session.query(Step).order_by(Step.order).all()
        total_min = 0
        self.steps = []
        for step in steps:
            total_min += step.timer
            self.steps.append((total_min, step))

    def start(self, cur_time=datetime.now()):
        if self.running:
            return

        self.refresh_steplist()
        self.running = True
        self._prev_time = datetime.now()

    def stop(self):
        if not self.running:
            return

        self.running = False
        self.pause = False

    def process(self, cur_time=datetime.now()):
        if self.running:
            if not self.pause:
                self.progress += cur_time - self._prev_time
        else:
            self.progress = timedelta()

        self._prev_time = cur_time

    def toggle_pause(self, cur_time=datetime.now()):
        self.pause = not self.pause

    @property
    def cur_step(self):
        for total_min, step in self.steps:
            if td_to_min(self.progress) < total_min:
                return step

    @property
    def cur_setpoint(self):
        return self.cur_step.temp
