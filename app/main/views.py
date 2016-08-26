from . import main
from ..control import TempController, set_mixer_output
from .. import models


@main.route('/')
def index():
    return 'Hello World'

