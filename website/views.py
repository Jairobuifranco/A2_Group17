from flask import Blueprint, abort, render_template, url_for

from . import db
from .models import Event


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    events = db.session.scalars(db.select(Event).order_by(Event.start_time)).all()
    return render_template('index.html', events=events)


@main_bp.route('/events/<int:event_id>')
def event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    image_url = event.image_url
    if image_url:
        if image_url.startswith(('http://', 'https://')):
            resolved_image_url = image_url
        else:
            normalized_path = image_url.lstrip('/')
            if normalized_path.startswith('static/'):
                normalized_path = normalized_path[len('static/'):]
            resolved_image_url = url_for('static', filename=normalized_path)
    else:
        resolved_image_url = url_for('static', filename='img/hero1.jpg')

    return render_template('event.html', event=event, event_image_url=resolved_image_url)
