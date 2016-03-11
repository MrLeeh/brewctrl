"""
sequence.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from datetime import datetime, timedelta

from .config import DELTA_TEMP
from .models import Step, State


def td_to_min(td: timedelta):
    """ Convert Timedelta object to minutes """
    return td.seconds / 60


def td_to_min_s(td: timedelta):
    mins = td.seconds // 60
    secs = td.seconds % 60
    return mins, secs


class Sequence:

    def __init__(self):

        self.cur_time = None
        self.start_time = None
        self.cur_step_nr = -1

        # status attributes
        self.running = False
        self.steps = []

    def start(self, cur_time=datetime.now()):
        if self.running:
            return

        self.cur_time = datetime.now()
        self.start_time = self.cur_time

        # get all steps and set first one as current step
        self.steps = Step.query.order_by(Step.order).all()

        for step in self.steps:
            step.state = State.INACTIVE
            step.elapsed_time = timedelta()

        self.cur_step_nr = 0
        step = self.steps[0]
        step.state = State.HEATUP
        self.running = True

    def stop(self):
        if not self.running:
            return

        self.running = False

    def process(self, temp, cur_time=datetime.now()):
        self.cur_time = cur_time

        if not self.running:
            return

        if self.start_time is None:
            self.start_time = self.cur_time

        step = self.steps[self.cur_step_nr]

        if step.state == State.INACTIVE:
            step.state = State.HEATUP

        if step.state == State.HEATUP:
            # if current temperature nearly steps setpoint begin counting
            if step.setpoint + DELTA_TEMP >= temp >= step.setpoint - DELTA_TEMP:
                step.elapsed_time = timedelta()
                step.state = State.REST
                step.start_time = self.cur_time

        elif step.state == State.REST:
            step.elapsed_time = self.cur_time - step.start_time
            if td_to_min(step.elapsed_time) >= step.timer:
                step.state = State.DONE

        elif step.state == State.DONE:
                self.cur_step_nr += 1

        if self.cur_step_nr >= len(self.steps):
            self.running = False
            self.done = True

    @property
    def cur_step(self):
        if not self.running:
            return None
        return self.steps[self.cur_step_nr]

    @property
    def setpoint(self):
        if not self.running:
            return None
        return self.cur_step.setpoint
