"""Initialize app."""
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import flask
from Applications.FlaskApp.errorpages import *

"""Construct the core application."""

app = Flask(__name__,
               instance_relative_config=False)

app.config.from_object('Applications.config.Config')

with app.app_context():

    # Import main Blueprint
    from Applications.FlaskApp.flask_app import main_bp
    app.register_blueprint(main_bp)

    # Import Error Pages
    app.register_error_handler(404,page_not_found)
    app.register_error_handler(403,page_not_allowed)
    app.register_error_handler(500,internal_error)
    app.register_error_handler(501,unhandled_exception)

    # Compile assets
    from Applications.assets import compile_assets
    compile_assets(app)

#server = app.server
#app.config.suppress_callback_exceptions = True
