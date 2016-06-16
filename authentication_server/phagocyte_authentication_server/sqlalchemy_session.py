#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This is an SQLAlchemy session handler for Flask

Original work by Alex Grönholm, found on https://gist.github.com/agronholm/7249102
"""

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker


class SQLAlchemy:
    engine = None
    session = None

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.extensions['sqlalchemy'] = self

        self.engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        self.session = scoped_session(sessionmaker(self.engine))
        app.teardown_appcontext(self.close_session)

    # noinspection PyUnresolvedReferences
    def close_session(self, response_or_exc):
        try:
            if response_or_exc is None and self.session.is_active:
                self.session.commit()
        finally:
            self.session.remove()

        return response_or_exc
