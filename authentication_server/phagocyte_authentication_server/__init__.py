#!/usr/bin/python3
import os
from flask import Flask
from flask_script import Manager
from flask_jwt import JWT

from phagocyte_authentication_server.auth import authenticate, identity
from phagocyte_authentication_server.commands import Server
from phagocyte_authentication_server.models import db, Base


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


app = Flask("phagocyte_auth")


app.config["CONFIG_PATH"] = os.environ.get("PHAGOCYTE_AUTH_SERVER", os.path.join(app.root_path, "config.cfg"))
app.config.from_pyfile(app.config["CONFIG_PATH"])

db.init_app(app)

with app.app_context():
    Base.metadata.create_all(db.engine)


jwt = JWT(app, authenticate, identity)

manager = Manager(app, with_default_commands=False)

manager.add_command("runserver", Server(
    debug=app.config.get("DEBUG", False),
    host=app.config.get("HOST", "127.0.0.1"),
    port=app.config.get("PORT", 8000)
))


from . import views
