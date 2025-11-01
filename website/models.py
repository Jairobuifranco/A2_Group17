from datetime import datetime, timezone
from flask_login import UserMixin
from . import db  # the SQLAlchemy() you init in website/__init__.py


# -------------------- Users --------------------

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # relationships
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"


# -------------------- Events --------------------

class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150))
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default="Open")
    category = db.Column(db.String(60))
    image_url = db.Column(db.String(255))

    comments = db.relationship("Comment", back_populates="event", cascade="all, delete-orphan")
    orders   = db.relationship("Order",   back_populates="event", cascade="all, delete-orphan")

    @property
    def is_expired(self) -> bool:
        """Return True when the event end (or start) time is in the past."""
        reference = self.end_time or self.start_time
        if reference is None:
            return False
        return reference < datetime.utcnow()

    @property
    def display_status(self) -> str:
        """Status label with automatic expiry handling."""
        base_status = (self.status or '').strip()
        if self.is_expired and base_status.lower() not in {'cancelled', 'expired'}:
            return 'Expired'
        return base_status or 'Open'


# -------------------- Comments --------------------

class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    user  = db.relationship("User",  back_populates="comments")
    event = db.relationship("Event", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment {self.id} user={self.user_id} event={self.event_id}>"


# -------------------- Orders (bookings) --------------------

class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    # ensure these columns exist in the table (add them if your DB is older)
    ticket_type = db.Column(db.String(20), nullable=False, default="General")
    created_at  = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_cancelled = db.Column(db.Boolean, nullable=False, default=False)

    # relationships — use back_populates on both sides (no backref here)
    event = db.relationship("Event", back_populates="orders")
    user  = db.relationship("User",  back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order {self.id} user={self.user_id} event={self.event_id} qty={self.quantity}>"


# -------------------- Booking audit (optional) --------------------

class BookingEvent(db.Model):
    __tablename__ = "booking_events"
    # created PRIMARY KEY event_id; keeping that mapping:
    event_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(20), nullable=False)  # CREATED|UPDATED|STATUS_CHANGE|DELETED|NOTE
    old_status = db.Column(db.String(40))
    new_status = db.Column(db.String(40))
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    event_note = db.Column(db.Text)
    occurred_at_utc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actor = db.Column(db.String(80))

    def __repr__(self) -> str:
        return f"<BookingEvent {self.event_id} type={self.event_type} booking={self.booking_id}>"