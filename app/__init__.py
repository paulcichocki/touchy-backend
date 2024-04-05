# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.secret_key = 'mF3LNkxqns4umFcFrXFvh1VqgmSYgVBa'

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix=app.config['PREFIX_URL'])

    return app
