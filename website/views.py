from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from . import db
from .models import Event, Order
from .forms import EventForm, BookingForm


main_bp = Blueprint('main', __name__)

GENRE_OPTIONS = [
    "Electronic",
    "Rock",
    "Jazz",
    "Classical",
    "Latin",
    "Hip Hop",
    "Other",
]

QUICK_FILTER_OPTIONS = [
    ("today", "Today"),
    ("week", "This Week"),
    ("under50", "Under $50"),
]


def _resolve_event_datetimes(form: EventForm):
    """Combine date/time fields and ensure end after start."""
    start_date = form.start_date.data
    start_time_value = form.start_time.data
    end_time_value = form.end_time.data

    if not all([start_date, start_time_value, end_time_value]):
        return None, None, True

    start_datetime = datetime.combine(start_date, start_time_value)
    end_datetime = datetime.combine(start_date, end_time_value)

    if end_datetime <= start_datetime:
        form.end_time.errors.append('End time must be after start time.')
        return None, None, False

    return start_datetime, end_datetime, True


@main_bp.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    genre_filter = request.args.get('genre', '').strip()
    quick_filter = request.args.get('quick', '').strip().lower()
    statement = db.select(Event).order_by(Event.start_time)
    if search_query:
        pattern = f"%{search_query}%"
        statement = statement.where(
            or_(
                Event.title.ilike(pattern),
                Event.venue.ilike(pattern),
                Event.category.ilike(pattern),
                Event.description.ilike(pattern),
            )
        )
    if genre_filter:
        statement = statement.where(Event.category.ilike(genre_filter))
    now = datetime.utcnow()
    if quick_filter == 'today':
        start_of_day = datetime.combine(now.date(), datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        statement = statement.where(
            Event.start_time >= start_of_day,
            Event.start_time < end_of_day,
        )
    elif quick_filter == 'week':
        end_of_range = now + timedelta(days=7)
        statement = statement.where(
            Event.start_time >= now,
            Event.start_time < end_of_range,
        )
    elif quick_filter == 'under50':
        statement = statement.where(Event.price <= Decimal('50'))
    quick_filter_label = next(
        (label for value, label in QUICK_FILTER_OPTIONS if value == quick_filter),
        None,
    )
    events = db.session.scalars(
        statement
    ).all()
    upcoming_events = [
        event for event in events
        if not event.is_expired
    ]
    upcoming_events.sort(
        key=lambda event: (
            0 if 'open' in (event.display_status or '').lower() else 1,
            event.start_time or datetime.max,
        )
    )
    past_events = [
        event for event in events
        if event.is_expired
    ]
    featured_events = upcoming_events[:2] if upcoming_events else events[:2]
    return render_template(
        'index.html',
        events=events,
        upcoming_events=upcoming_events,
        past_events=past_events,
        featured_events=featured_events,
        search_query=search_query,
        genres=GENRE_OPTIONS,
        selected_genre=genre_filter,
        quick_filters=QUICK_FILTER_OPTIONS,
        quick_filter=quick_filter,
        quick_filter_label=quick_filter_label,
    )


@main_bp.route('/events/<int:event_id>')
def event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    booking_form = BookingForm()
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

    return render_template('event.html', event=event, event_image_url=resolved_image_url, booking_form=booking_form)


@main_bp.route('/bookings')
@login_required
def bookings():
    orders = db.session.scalars(
        db.select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.event))
        .order_by(Order.created_at.desc())
    ).all()

    return render_template('bookings.html', orders=orders)


@main_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    form.submit.label.text = 'Create Event'
    template_context = {
        'form': form,
        'form_action': url_for('main.create_event'),
        'page_title': 'Create Event',
        'page_heading': 'Create a New Event',
        'page_subheading': 'Provide the event details below and publish instantly.',
        'back_url': url_for('main.index'),
        'back_label': 'Back to Events',
        'active_nav': 'create',
        'is_edit': False,
    }

    if form.validate_on_submit():
        start_datetime, end_datetime, is_valid = _resolve_event_datetimes(form)
        if not is_valid:
            return render_template('create.html', **template_context)
        event = Event(
            title=form.title.data,
            venue=form.venue.data,
            description=form.description.data,
            start_time=start_datetime,
            end_time=end_datetime,
            price=form.price.data,
            status=form.status.data,
            category=form.category.data,
            image_url=form.image_url.data,
            user_id=current_user.id,
        )

        db.session.add(event)
        db.session.commit()

        flash('Event created successfully!', 'success')
        return redirect(url_for('main.event', event_id=event.id))

    return render_template('create.html', **template_context)


@main_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    if event.user_id != current_user.id:
        flash('You are not authorized to edit this event.')
        return redirect(url_for('main.event', event_id=event.id))

    form = EventForm(obj=event)
    form.submit.label.text = 'Update Event'

    if request.method == 'GET':
        if event.start_time:
            form.start_date.data = event.start_time.date()
            form.start_time.data = event.start_time.time()
        if event.end_time:
            form.end_time.data = event.end_time.time()
        elif event.start_time:
            form.end_time.data = event.start_time.time()

    template_context = {
        'form': form,
        'form_action': url_for('main.edit_event', event_id=event.id),
        'page_title': f'Edit {event.title}',
        'page_heading': f'Edit "{event.title}"',
        'page_subheading': 'Update the event details and save changes.',
        'back_url': url_for('main.event', event_id=event.id),
        'back_label': 'Back to Event',
        'active_nav': 'create',
        'is_edit': True,
    }

    if form.validate_on_submit():
        start_datetime, end_datetime, is_valid = _resolve_event_datetimes(form)
        if not is_valid:
            return render_template('create.html', **template_context)

        event.title = form.title.data
        event.venue = form.venue.data
        event.description = form.description.data
        event.start_time = start_datetime
        event.end_time = end_datetime
        event.price = form.price.data
        event.status = form.status.data
        event.category = form.category.data
        event.image_url = form.image_url.data

        db.session.commit()

        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.event', event_id=event.id))

    return render_template('create.html', **template_context)


@main_bp.route('/events/<int:event_id>/book', methods=['POST'])
@login_required
def book_event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    form = BookingForm()
    if not form.validate_on_submit():
        flash('Please select a valid ticket quantity.', 'danger')
        return redirect(url_for('main.event', event_id=event.id))

    if event.is_expired:
        flash('This event has already concluded. Booking is unavailable.', 'warning')
        return redirect(url_for('main.event', event_id=event.id))

    order = Order(user=current_user, event=event, quantity=form.quantity.data)
    db.session.add(order)
    db.session.commit()

    flash('Tickets booked successfully! View them in your bookings.', 'success')
    return redirect(url_for('main.bookings'))
