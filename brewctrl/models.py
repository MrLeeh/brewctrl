"""
models.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from sqlalchemy import Boolean, Column
from sqlalchemy import DateTime, Integer, String, Text, Float, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# class Receipe(Base):

#     id = Column(Integer, primary_key=True)
#     name = Column(String(255))
#     description = Column(Text)


class Step(Base):

    __tablename__ = 'steps'
    id = Column(Integer, primary_key=True)
    order = Column(Integer())
    name = Column(String(80))
    temp = Column(Integer())
    timer = Column(Integer())
    comment = Column(Text())

    def __repr__(self):
        return '<{self.__class__.__name__}: {self.id}{self.name}>'.format(
            self=self)


class TempCtrl(Base):
    __tablename__ = 'tempctrl'
    id = Column(Integer, primary_key=True)
    setpoint = Column(Float, default=50.0)
    kp = Column(Float, default=10.0)
    tn = Column(Float, default=180.0)
    mode = Column(String(80), default='auto')
    duty_cycle = Column(Float, default=60.0)
    manual_power = Column(Float, default=50.0)


class ProcessData(Base):

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
