from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from sqlalchemy import text

from . import db
from .models import Event, Order
from .forms import EventForm, BookingForm

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# basic config
BNE_TZ = ZoneInfo("Australia/Brisbane")          # main timezone for display
BRISBANE_TZ = timezone(timedelta(hours=10))      # fallback offset if needed
MAX_CAPACITY = 500                               # max tickets per event



main_bp = Blueprint('main', __name__)

def _to_bne_string(ts):
    """Returns a Brisbane time string for a given UTC/ISO timestamp."""
    if ts is None:
        return ""
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", ""))
        except ValueError:
            return ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
    return dt.astimezone(BNE_TZ).strftime("%Y-%m-%d %H:%M:%S")


def recalc_event_status(event_id: int):
    """Recalculates how many tickets are sold for an event and sets its status to 'Open' or 'Sold Out'."""
    qty_stmt = text("""
        SELECT COALESCE(SUM(quantity), 0) AS total_qty
        FROM "order"
        WHERE event_id = :eid AND is_cancelled = 0
    """)
    row = db.session.execute(qty_stmt, {"eid": event_id}).fetchone()
    total_qty = row.total_qty or 0

    new_status = "Sold Out" if total_qty >= MAX_CAPACITY else "Open"
    db.session.execute(text("""
        UPDATE event SET status = :new_status WHERE id = :eid
    """), {"new_status": new_status, "eid": event_id})
    db.session.commit()


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
    )


@main_bp.get("/events/<int:event_id>")
def event(event_id: int):
    """Shows one event page with its details, booking state, and comments."""
    this_event = db.session.get(Event, event_id)
    if not this_event:
        abort(404)

    booking_form = BookingForm()

    # use the row we just loaded
    image_url = this_event.image_url
    if image_url:
        if image_url.startswith(("http://", "https://")):
            resolved_image_url = image_url
        else:
            normalized_path = image_url.lstrip("/")
            if normalized_path.startswith("static/"):
                normalized_path = normalized_path[len("static/"):]
            resolved_image_url = url_for("static", filename=normalized_path)
    else:
        resolved_image_url = url_for("static", filename="img/hero1.jpg")

    # pass the row to the template
    return render_template(
        "event.html",
        event=this_event,
        event_image_url=resolved_image_url,
        booking_form=booking_form,
    )


@main_bp.get("/bookings")
@login_required
def bookings():
    rows = db.session.execute(
        text("""
            SELECT
              o.id            AS order_id,
              o.quantity      AS quantity,
              o.ticket_type   AS ticket_type,
              o.is_cancelled  AS is_cancelled,
              o.created_at    AS booked_at,
              e.title         AS event_title,
              e.image_url     AS image_url
            FROM "order" o
            JOIN event e ON e.id = o.event_id
            WHERE o.user_id = :uid
              AND o.is_cancelled = 0
            ORDER BY o.created_at DESC
        """),
        {"uid": current_user.id}
    ).mappings().all()

    return render_template("bookings.html", bookings=rows)


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

@main_bp.route("/orders/<int:event_id>/create", methods=["POST", "GET"])
@login_required
def create_order(event_id: int):
    """Creates a booking for an event if there are enough tickets left."""
    # block direct GET access (we only want POST from the form)
    if request.method == "GET":
        return redirect(url_for("main.event", event_id=event_id))

    # fake user for now (we don't have login wired yet)
    user_id = int(request.form.get("user_id", 1))

    # requested quantity
    try:
        qty = int(request.form.get("qty", 1))
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1

    # General / VIP etc.
    ticket_type = request.form.get("ticket_type", "General")

    # how many tickets are already booked (not cancelled)
    current_row = db.session.execute(text("""
        SELECT COALESCE(SUM(quantity), 0) AS total_qty
        FROM "order"
        WHERE event_id = :eid AND is_cancelled = 0
    """), {"eid": event_id}).fetchone()
    already_booked = current_row.total_qty or 0
    capacity_left = MAX_CAPACITY - already_booked

    # reject if no capacity or if they asked for too many
    if capacity_left <= 0:
        flash("Sorry, this event is not accepting bookings.", "warning")
        return redirect(url_for("main.event", event_id=event_id))
    if qty > capacity_left:
        flash(f"Only {capacity_left} tickets left. Please reduce your quantity.", "warning")
        return redirect(url_for("main.event", event_id=event_id))

    # save the booking in UTC time (we convert to Brisbane in the template)
    created_utc = datetime.now(timezone.utc)
    db.session.execute(text("""
        INSERT INTO "order" (quantity, created_at, user_id, event_id, ticket_type, is_cancelled)
        VALUES (:q, :created_at, :uid, :eid, :tt, 0)
    """), {"q": qty, "created_at": created_utc, "uid": user_id, "eid": event_id, "tt": ticket_type})
    db.session.commit()

    # update event status now that we've added this booking
    recalc_event_status(event_id)

    flash("Booking created!", "success")
    return redirect(url_for("main.bookings"))


@main_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id: int):
    """Cancels a booking and gives those tickets back to the event."""
    # find which event this order belongs to
    info_row = db.session.execute(text("""
        SELECT event_id FROM "order" WHERE id = :oid LIMIT 1
    """), {"oid": order_id}).fetchone()
    if not info_row:
        flash("Booking not found.", "warning")
        return redirect(url_for("main.bookings"))

    event_id = info_row.event_id

    # mark this booking as cancelled instead of deleting it
    db.session.execute(text("""
        UPDATE "order" SET is_cancelled = 1 WHERE id = :oid
    """), {"oid": order_id})
    db.session.commit()

    # event might reopen if enough tickets got freed
    recalc_event_status(event_id)

    flash("Booking cancelled.", "success")
    return redirect(url_for("main.bookings"))

@main_bp.post("/events/<int:event_id>/comments")
@login_required
def add_comment(event_id: int):
    """Adds a new comment to the event page."""
    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be empty.")
        return redirect(url_for("main.event", event_id=event_id))

    # store comment using fake user_id=1 for now
    db.session.execute(text("""
        INSERT INTO comment (body, created_at, user_id, event_id)
        VALUES (:b, datetime('now'), :u, :e)
    """), {"b": body, "u": 1, "e": event_id})
    db.session.commit()

    flash("Comment posted.")
    return redirect(url_for("main.event", event_id=event_id))
