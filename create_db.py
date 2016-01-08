#!/usr/bin/env python

"""
create_db.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

import os.path

from sqlalchemy import create_engine
from migrate.versioning import api

from brewctrl.config import SQLALCHEMY_DATABASE_URI
from brewctrl.config import SQLALCHEMY_MIGRATE_REPO
from brewctrl.models import Base


engine = create_engine('sqlite:///brewctrl.db', echo=True)
Base.metadata.create_all(engine)

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(
        SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO,
        api.version(SQLALCHEMY_MIGRATE_REPO)
    )
