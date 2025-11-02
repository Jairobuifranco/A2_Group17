# import flask - from 'package' import 'Class'
from flask import Flask
try:
    from bootstrap_flask import Bootstrap5
except ModuleNotFoundError:
    Bootstrap5 = None
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

# create a function that creates a web application
# a web server will run this web application
def create_app(config: dict | None = None):
    # Construct the Flask application and register extensions/blueprints.

    app = Flask(__name__)  # this is the name of the module/package that is calling this app
    app.config.from_mapping(
        SECRET_KEY='somesecretkey',
        SQLALCHEMY_DATABASE_URI='sqlite:///sitedata.sqlite',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config:
        app.config.update(config)
    # initialise db with flask app
    db.init_app(app)

    if Bootstrap5:
        Bootstrap5(app)
    
    # initialise the login manager
    login_manager = LoginManager()
    
    # set the name of the login function that lets user login
    # in our case it is auth.login (blueprintname.viewfunction name)z
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # create a user loader function takes userid and returns User
    # Importing inside the create_app function avoids circular references
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
       return db.session.scalar(db.select(User).where(User.id==user_id))

    from . import views
    app.register_blueprint(views.main_bp)

    try:
        from . import auth
    except ModuleNotFoundError as exc:  # dependency missing; run without auth routes
        app.logger.warning("Skipping auth blueprint because '%s' is not available", exc.name)
    else:
        app.register_blueprint(auth.auth_bp)

    from flask import render_template

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error("Unhandled exception: %s", error)
        return render_template('errors/500.html'), 500

    return app
