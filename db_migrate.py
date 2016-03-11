#!/usr/bin/env python

"""
db_migrate.py,

copyright (c) 2016 by Stefan Lehmann,
licensed under the MIT license

"""

import imp

from migrate.versioning import api
from brewctrl.config import SQLALCHEMY_DATABASE_URI
from brewctrl.config import SQLALCHEMY_MIGRATE_REPO
from brewctrl.app import db

v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % (v+1))
tmp_module = imp.new_module('old_model')
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

exec(old_model, tmp_module.__dict__)
script = api.make_update_script_for_model(
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO,
    tmp_module.meta, db.metadata
)

open(migration, "wt").write(script)

api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

print('New migration saved as ' + migration)
print('Current database version: ' + str(v))
