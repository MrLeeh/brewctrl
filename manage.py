#! /usr/bin/env python3
"""
manage.py,

copyright (c) 2015 by Stefan Lehmann,
licensed under the MIT license

"""

import os
from app import create_app, db
from app.models import TempCtrl
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, TempCtrl=TempCtrl)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def run(host='0.0.0.0', port=5000, user_reloader=True):
    """
    Run the Flask development server with websocket support.

    """
    port = int(port)
    from app import socketio
    socketio.run(
        app,
        host=host,
        port=port,
    )

@manager.command
def test():
    """ Run unit tests """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
