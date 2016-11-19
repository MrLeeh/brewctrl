#!/usr/bin/env bash
source venv/bin/activate
exec gunicorn --worker-class eventlet -w 1 wsgi:app -blocalhost:5000