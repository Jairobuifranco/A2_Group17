from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pathlib import Path
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo  
except Exception:
    ZoneInfo = None

# Bootstrap import
try:
    from flask_bootstrap import Bootstrap5
except ModuleNotFoundError:
    Bootstrap5 = None

# shared db instance
db = SQLAlchemy()


def create_app():
    # create our Flask app
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # basic settings for local testing
    app.debug = True
    app.secret_key = "somesecretkey"

    # make sure the instance folder exists for the SQLite file
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # use main SQLite DB stored in /instance folder
    db_file = (Path(app.instance_path) / "sitedata.sqlite").absolute()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # init database + bootstrap 
    db.init_app(app)
    if Bootstrap5:
        Bootstrap5(app)

    # login manager setup
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # import user model so we can load users later
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # gets user from the DB by ID
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # jinja filter to show time in Brisbane timezone
    def _to_brisbane(val):
        """Converts UTC or ISO datetime to Brisbane time (YYYY-MM-DD HH:MM)."""
        if val is None:
            return ""
        if isinstance(val, str):
            s = val.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                return val
        else:
            dt = val

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        if ZoneInfo:
            dt_bris = dt.astimezone(ZoneInfo("Australia/Brisbane"))
            return dt_bris.strftime("%Y-%m-%d %H:%M")

        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")

    # add the filter so we can use | bris in html
    app.jinja_env.filters["bris"] = _to_brisbane

    # register main blueprint (main routes)
    from . import views
    app.register_blueprint(views.main_bp)

    # register auth blueprint if available
    try:
        from . import auth
    except ModuleNotFoundError as exc:
        app.logger.warning("Skipping auth blueprint: %s not found", exc.name)
    else:
        app.register_blueprint(auth.auth_bp, url_prefix="/auth")

    return app