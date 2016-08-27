#!/bin/bash
cd /home/pi/python/brewctrl
source venv/bin/activate

export FLASK_CONFIG=development
exec python manage.py run
