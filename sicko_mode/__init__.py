import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True, template_folder='templates')

    if test_config is None:
        # load the instance config, if it exists, when not testing
        # Load configurations from .env file
        load_dotenv()
    else:
        # load the test config if passed in
        app.config.update(test_config)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "sicko_secret_key")

    # ensure the instance folder exists
    # try:
    #    os.makedirs(app.instance_path)
    # except OSError:
    #    pass

    @app.route('/')
    def start():
        return redirect(url_for('auth.login'))

    # apply the blueprints to the app
    from sicko_mode import database, auth, clinic

    app.register_blueprint(auth.bp)
    app.register_blueprint(clinic.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    return app
