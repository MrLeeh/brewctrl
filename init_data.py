#!-*- coding: utf-8 -*-
"""
:author: Stefan Lehmann <stefan.st.lehmann@gmail.com>

"""
from app import create_app, db
from app.models import Step


app = create_app('default')

with app.app_context():
    # delete old step templates
    for step in Step.query.filter(Step.template):
        db.session.delete(step)
    db.session.commit()

    # add step templates
    step_templates = [
        Step(
            name='Eiweißrast',
            setpoint=54
        ),
        Step(
            name='Maltoserast',
            setpoint=63
        ),
        Step(
            name='Verzuckerungsrast',
            setpoint=72
        ),
        Step(
            name='Abmaischen',
            setpoint=78
        )
    ]

    for step in step_templates:
        step.template = True
        db.session.add(step)

    db.session.commit()
