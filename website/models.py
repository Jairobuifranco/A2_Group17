from datetime import datetime

from flask_login import UserMixin

from . import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    orders = db.relationship('Order', back_populates='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='user', cascade='all, delete-orphan')


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    general_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    general_tickets = db.Column(db.Integer, nullable=False, default=1)
    vip_price = db.Column(db.Integer, nullable=False, default=0)
    vip_tickets = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(40), nullable=False, default='Open')
    category = db.Column(db.String(60))
    image_url = db.Column(db.String(255))

    # Add user id into event table as FK #
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, default=1)
    user = db.relationship('User', backref='events')

    comments = db.relationship('Comment', back_populates='event', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='event', cascade='all, delete-orphan')

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


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    user = db.relationship('User', back_populates='comments')
    event = db.relationship('Event', back_populates='comments')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    user = db.relationship('User', back_populates='orders')
    event = db.relationship('Event', back_populates='orders')