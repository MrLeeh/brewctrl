"""
models.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""
from sqlalchemy import Boolean, Column
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class receipe(Base):

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
