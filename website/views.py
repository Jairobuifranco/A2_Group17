from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy import text
from . import db
from .models import Event
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# basic config
BNE_TZ = ZoneInfo("Australia/Brisbane")          # main timezone for display
BRISBANE_TZ = timezone(timedelta(hours=10))      # fallback offset if needed
MAX_CAPACITY = 500                               # max tickets per event

main_bp = Blueprint("main", __name__)


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


@main_bp.get("/")
def index():
    """Shows all events on the home page, newest first."""
    events = db.session.scalars(
        db.select(Event).order_by(Event.start_time.desc())
    ).all()
    return render_template("index.html", events=events)


@main_bp.get("/events/<int:event_id>")
def event(event_id: int):
    """Shows one event page with its details, booking state, and comments."""
    this_event = db.session.get(Event, event_id)
    if not this_event:
        abort(404)

    # pick an image for the event (fallback if missing)
    img = getattr(this_event, "image_url", None)
    if img and not img.startswith(("http://", "https://")):
        img = url_for("static", filename=img.lstrip("/").replace("static/", ""))
    if not img:
        img = url_for("static", filename="img/hero1.jpg")

    # load comments for this event so newest first
    comments = []
    try:
        sql = text("""
            SELECT body, created_at, user_id
            FROM comment
            WHERE event_id = :eid
            ORDER BY id DESC
        """)
        comments = [
            dict(row)
            for row in db.session.execute(sql, {"eid": event_id}).mappings().all()
        ]
    except Exception:
        comments = []  # if comment table doesn't exist etc.

    return render_template("event.html", event=this_event, event_image_url=img, comments=comments)


@main_bp.route("/orders/<int:event_id>/create", methods=["POST", "GET"])
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


@main_bp.get("/bookings")
def bookings():
    """Shows the current user's active bookings (not cancelled)."""
    uid = 1  # placeholder user until login is added
    rows = db.session.execute(text("""
        SELECT o.id AS order_id, o.quantity, o.ticket_type, o.is_cancelled,
               o.created_at AS booked_at, e.title AS event_title, e.image_url
        FROM "order" o
        JOIN event e ON e.id = o.event_id
        WHERE o.user_id = :uid AND o.is_cancelled = 0
        ORDER BY o.created_at DESC
    """), {"uid": uid}).mappings().all()
    return render_template("bookings.html", bookings=rows)


@main_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
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