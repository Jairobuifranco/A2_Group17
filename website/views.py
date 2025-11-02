from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from . import db
from .models import Comment, Event, Order
from .forms import BookingForm, CommentForm, EventForm, EVENT_CATEGORY_OPTIONS


main_bp = Blueprint('main', __name__)

GENRE_OPTIONS = EVENT_CATEGORY_OPTIONS

QUICK_FILTER_OPTIONS = [
    ("today", "Today"),
    ("week", "This Week"),
    ("under50", "Under $50"),
]

def _configure_booking_form(form: BookingForm, event: Event) -> tuple[int, int]:
    """Set ticket options and quantity choices; returns (available_general, available_vip)."""
    general_available = event.general_remaining_tickets
    vip_available = event.vip_remaining_tickets
    ticket_choices = []
    if general_available > 0:
        ticket_choices.append((
            "general",
            f"General Admission — ${event.general_price:.2f} ({general_available} left)"
        ))
    if vip_available > 0:
        vip_price = event.vip_price if event.vip_price is not None else event.general_price
        ticket_choices.append((
            "vip",
            f"VIP — ${vip_price:.2f} ({vip_available} left)"
        ))

    valid_values = {choice[0] for choice in ticket_choices}
    submitted_raw = getattr(form.ticket_type, "raw_data", None)

    if ticket_choices:
        form.ticket_type.choices = ticket_choices
        if form.ticket_type.data not in valid_values:
            if not submitted_raw:
                form.ticket_type.data = ticket_choices[0][0]
    else:
        # No tickets remaining; keep default choices to avoid validation issues.
        form.ticket_type.choices = [("general", "General Admission")]
        form.ticket_type.data = "general"

    selected_value = form.ticket_type.data if form.ticket_type.data in valid_values else None

    if selected_value == "general":
        available_for_selection = general_available
    elif selected_value == "vip":
        available_for_selection = vip_available
    else:
        available_for_selection = 0
    if available_for_selection > 0:
        max_selectable = min(8, available_for_selection)
        form.quantity.choices = [(i, str(i)) for i in range(1, max_selectable + 1)]
    else:
        form.quantity.choices = []

    return general_available, vip_available


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
    # Render the landing page with optional search and filter results.
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
        statement = statement.where(Event.general_price <= Decimal('50'))
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


def _render_event(event: Event, booking_form: BookingForm | None = None, comment_form: CommentForm | None = None):
    """Render the event page with the provided forms."""
    if booking_form is None:
        booking_form = BookingForm()
    if comment_form is None:
        comment_form = CommentForm()

    general_available, vip_available = _configure_booking_form(booking_form, event)

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

    can_manage = current_user.is_authenticated and event.owner_id == current_user.id

    return render_template(
        'event.html',
        event=event,
        event_image_url=resolved_image_url,
        booking_form=booking_form,
        comment_form=comment_form,
        can_manage=can_manage,
        general_available=general_available,
        vip_available=vip_available,
    )


@main_bp.route('/events/<int:event_id>')
def event(event_id: int):
    # Display details for a single event including booking options.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    return _render_event(event)


@main_bp.route('/bookings')
@login_required
def bookings():
    # Show the authenticated user's booking history.
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
    # Allow an authenticated user to create a new event.
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
            general_price=form.general_price.data,
            vip_price=form.vip_price.data if form.vip_price.data is not None else None,
            category=form.category.data,
            image_url=form.image_url.data,
            owner=current_user,
            status='Open',
            general_capacity=form.general_capacity.data,
            vip_capacity=form.vip_capacity.data,
        )

        db.session.add(event)
        db.session.commit()

        flash('Event created successfully!', 'success')
        return redirect(url_for('main.event', event_id=event.id))

    return render_template('create.html', **template_context)


@main_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id: int):
    # Permit the owner to update an existing event's details.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)

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
        'event': event,
    }

    if form.validate_on_submit():
        start_datetime, end_datetime, is_valid = _resolve_event_datetimes(form)
        if not is_valid:
            return render_template('create.html', **template_context)
        if form.general_capacity.data < event.general_tickets_sold:
            form.general_capacity.errors.append(
                f"General admission tickets cannot be lower than the {event.general_tickets_sold} already booked."
            )
            return render_template('create.html', **template_context)
        if form.vip_capacity.data < event.vip_tickets_sold:
            form.vip_capacity.errors.append(
                f"VIP tickets cannot be lower than the {event.vip_tickets_sold} already booked."
            )
            return render_template('create.html', **template_context)

        event.title = form.title.data
        event.venue = form.venue.data
        event.description = form.description.data
        event.start_time = start_datetime
        event.end_time = end_datetime
        event.general_price = form.general_price.data
        event.vip_price = form.vip_price.data if form.vip_capacity.data > 0 else None
        event.category = form.category.data
        event.image_url = form.image_url.data
        event.general_capacity = form.general_capacity.data
        event.vip_capacity = form.vip_capacity.data

        db.session.commit()

        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.event', event_id=event.id))

    return render_template('create.html', **template_context)


@main_bp.route('/events/<int:event_id>/book', methods=['POST'])
@login_required
def book_event(event_id: int):
    # Process ticket purchases for a specific event.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    form = BookingForm()
    _configure_booking_form(form, event)

    if not form.validate_on_submit():
        flash('Please select a valid ticket quantity.', 'danger')
        return redirect(url_for('main.event', event_id=event.id))

    ticket_type = form.ticket_type.data
    if ticket_type not in {'general', 'vip'}:
        flash('Invalid ticket type selected.', 'danger')
        return redirect(url_for('main.event', event_id=event.id))

    selected_available = (
        event.general_remaining_tickets if ticket_type == 'general' else event.vip_remaining_tickets
    )

    if selected_available <= 0 or event.is_expired or event.status.lower() in {'cancelled', 'sold out'}:
        flash('Bookings are unavailable for this event at this time.', 'warning')
        return redirect(url_for('main.event', event_id=event.id))

    if form.quantity.data > selected_available:
        flash(
            f'Only {selected_available} ticket{"s" if selected_available != 1 else ""} remain for this ticket type.',
            'warning'
        )
        return redirect(url_for('main.event', event_id=event.id))

    order = Order(user=current_user, event=event, quantity=form.quantity.data, ticket_type=ticket_type)
    db.session.add(order)
    db.session.commit()

    if event.total_remaining_tickets <= 0 and event.status.lower() != 'sold out':
        event.status = 'Sold Out'
        db.session.commit()

    ticket_label = 'VIP' if ticket_type == 'vip' else 'General Admission'
    flash(
        f'{ticket_label} tickets booked successfully! Order #{order.id:05d} is now in your bookings.',
        'success'
    )
    return redirect(url_for('main.bookings'))


@main_bp.route('/events/<int:event_id>/comments', methods=['POST'])
@login_required
def add_comment(event_id: int):
    # Persist a new comment on an event from the logged-in user.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, user=current_user, event=event)
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted successfully.', 'success')
        return redirect(url_for('main.event', event_id=event.id))

    flash('Please fix the errors before submitting your comment.', 'danger')
    return _render_event(event, comment_form=form)


@main_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id: int):
    # Mark an event as cancelled when requested by its owner.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)
    if event.status.lower() == 'cancelled':
        flash('This event is already cancelled.', 'info')
        return redirect(url_for('main.event', event_id=event.id))

    event.status = 'Cancelled'
    db.session.commit()
    flash('Event cancelled successfully. Attendees can no longer book tickets.', 'info')
    return redirect(url_for('main.event', event_id=event.id))


@main_bp.route('/events/<int:event_id>/sell-out', methods=['POST'])
@login_required
def mark_event_sold_out(event_id: int):
    # Allow the owner to manually set an event status to sold out.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)
    if event.status.lower() == 'sold out':
        flash('This event is already marked as sold out.', 'info')
        return redirect(url_for('main.event', event_id=event.id))

    event.status = 'Sold Out'
    db.session.commit()
    flash('Event marked as sold out.', 'success')
    return redirect(url_for('main.event', event_id=event.id))


@main_bp.route('/events/<int:event_id>/reopen', methods=['POST'])
@login_required
def reopen_event(event_id: int):
    # Reopen bookings for an event that previously sold out or was cancelled.
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if event.owner_id != current_user.id:
        abort(403)
    if event.status.lower() == 'open':
        flash('Event bookings are already open.', 'info')
        return redirect(url_for('main.event', event_id=event.id))
    if event.total_remaining_tickets <= 0:
        flash('Add more tickets before reopening bookings.', 'warning')
        return redirect(url_for('main.event', event_id=event.id))

    event.status = 'Open'
    db.session.commit()
    flash('Event reopened. Attendees can book tickets again.', 'success')
    return redirect(url_for('main.event', event_id=event.id))
