#! /usr/bin/env python3
"""
manage.py,

copyright (c) 2015 by Stefan Lehmann,
licensed under the MIT license

"""
import sys
import eventlet
import os
from app import create_app, db, brew_controller
from app.models import TempCtrlSettings, ProcessData, Step, Recipe
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


# only perform monkey patch in run mode otherwise
# shell won't be usable
if 'run' in sys.argv:
    eventlet.monkey_patch()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, TempCtrlSettings=TempCtrlSettings,
                brew_controller=brew_controller, ProcessData=ProcessData,
                Step=Step, Receipe=Recipe)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def run(host='0.0.0.0', port=5000, user_reloader=False):
    """
    Run the Flask development server with websocket support.

    """
    port = int(port)
    from app import socketio
    socketio.run(
        app,
        host=host,
        port=port,
        use_reloader=user_reloader
    )


@manager.command
def test():
    """ Run unit tests """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def coverage():
    """ Check coverage """
    import coverage
    cov = coverage.Coverage()
    cov.start()

    test()

    cov.stop()
    cov.save()

    cov.html_report()
    cov.report()


@manager.command
def init_data():
    from init_data import init_data
    init_data(app)

if __name__ == '__main__':
    manager.run()
