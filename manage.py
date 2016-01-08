#!/usr/bin/env python3

"""
manage.py,

copyright (c) 2015 by Stefan Lehmann,
licensed under the MIT license

"""

from flask.ext.script import Manager
from brewctrl.app import app, socketio


manager = Manager(app)


@manager.command
def run():
    """
    Runs the Flask development server with websocket support.

    """
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        use_reloader=False
    )


if __name__ == '__main__':
    manager.run()
