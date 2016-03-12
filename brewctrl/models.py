"""
models.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from enum import Enum
from datetime import timedelta

from sqlalchemy import Column, DateTime, Integer, String, Text, Float

from .app import db

# Base = declarative_base()


# class Receipe(Base):

#     id = Column(Integer, primary_key=True)
#     name = Column(String(255))
#     description = Column(Text)


class State(Enum):
    INACTIVE = 0
    HEATUP = 1
    REST = 2
    DONE = 3
    SKIPPED = 4


class Step(db.Model):

    __tablename__ = 'steps'
    id = Column(Integer, primary_key=True)
    order = Column(Integer())
    name = Column(String(80))
    setpoint = Column(Integer())
    timer = Column(Integer())
    comment = Column(Text())
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
    id = Column(Integer, primary_key=True)
    setpoint = Column(Float, default=50.0)
    kp = Column(Float, default=10.0)
    tn = Column(Float, default=180.0)
    mode = Column(String(80), default='auto')
    duty_cycle = Column(Float, default=60.0)
    manual_power = Column(Float, default=50.0)


class ProcessData(db.Model):

    __tablename__ = 'processdata'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    temp_setpoint = Column(Float())
    temp = Column(Float())


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
