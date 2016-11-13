from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from config import config


bootstrap = Bootstrap()
socketio = SocketIO()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    socketio.init_app(app)
    db.init_app(app)

    if app.debug:
        from flaskext.lesscss import lesscss
        lesscss(app)

    # init control
    from .hardware_control import init_control
    init_control(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
