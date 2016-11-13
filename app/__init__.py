from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from config import config



bootstrap = Bootstrap()
socketio = SocketIO()
db = SQLAlchemy()

from .brewcontroller import BrewController
brew_controller = BrewController()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    socketio.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    if app.debug:
        from flaskext.lesscss import lesscss
        lesscss(app)

    # init control
    brew_controller.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
