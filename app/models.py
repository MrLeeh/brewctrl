"""
models.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from enum import Enum
from datetime import timedelta
from . import db


class State(Enum):
    INACTIVE = 0
    HEATUP = 1
    REST = 2
    DONE = 3
    SKIPPED = 4


class Step(db.Model):

    __tablename__ = 'steps'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer())
    name = db.Column(db.String(80))
    setpoint = db.Column(db.Integer())
    timer = db.Column(db.Integer())
    comment = db.Column(db.Text())
    state = State.INACTIVE
    start_time = None
    elapsed_time = timedelta()

    def __repr__(self):
        return '<{self.__class__.__name__}: {self.id}{self.name}>'.format(
            self=self)

    @property
    def state_str(self):
        s = {
            State.INACTIVE: '',
            State.HEATUP: 'Aufheizen',
            State.REST: 'Rasten',
            State.DONE: 'Abgeschlossen',
            State.SKIPPED: 'Abgebrochen'
        }
        return s[self.state]

    @property
    def elapsed_time_str(self):
        td = self.elapsed_time
        if td == timedelta():
            return '-'
        else:
            return '{mins:02d}:{secs:02d}'.format(
                mins=td.seconds // 60,
                secs=td.seconds % 60
            )
        return self._elapsed_time_str


class TempCtrl(db.Model):

    __tablename__ = 'tempctrl'
    id = db.Column(db.Integer, primary_key=True)
    setpoint = db.Column(db.Float, default=50.0)
    kp = db.Column(db.Float, default=10.0)
    tn = db.Column(db.Float, default=180.0)
    mode = db.Column(db.String(80), default='auto')
    duty_cycle = db.Column(db.Float, default=60.0)
    manual_power = db.Column(db.Float, default=50.0)


class ProcessData(db.Model):

    __tablename__ = 'processdata'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    temp_setpoint = db.Column(db.Float())
    temp = db.Column(db.Float())


if __name__ == '__main__':
    from config import SQLALCHEMY_DATABASE_URI
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    steps = []
    steps.append(Step(order=0, name='Einmaischen', temp=54, timer=0))
    steps.append(Step(order=1, name='Eiweißrast', temp=57, timer=10))
    steps.append(Step(order=2, name='Maltoserast', temp=63, timer=45))
    steps.append(Step(order=3, name='Verzuckerungsrast', temp=67, timer=30))
    steps.append(Step(order=4, name='Abmaischen', temp=78, timer=10))

    for step in steps:
        session.add(step)

    session.commit()
