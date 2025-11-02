from datetime import datetime

from flask_login import UserMixin

from . import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(30), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)

    orders = db.relationship('Order', back_populates='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='user', cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='owner', cascade='all, delete-orphan')

    @property
    def name(self) -> str:
        """Convenience accessor used across templates."""
        return f"{self.first_name} {self.last_name}".strip()


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    general_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    vip_price = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(40), nullable=False, default='Open')
    category = db.Column(db.String(60))
    image_url = db.Column(db.String(255))
    general_capacity = db.Column(db.Integer, nullable=False, default=50)
    vip_capacity = db.Column(db.Integer, nullable=False, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    comments = db.relationship('Comment', back_populates='event', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='event', cascade='all, delete-orphan')
    owner = db.relationship('User', back_populates='events')

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
        if base_status.lower() == 'cancelled':
            return 'Cancelled'
        if base_status.lower() == 'sold out' or self.total_remaining_tickets <= 0:
            return 'Sold Out'
        if self.is_expired:
            return 'Inactive'
        return base_status or 'Open'

    @property
    def general_tickets_sold(self) -> int:
        return sum(order.quantity for order in self.orders if order.ticket_type == 'general')

    @property
    def vip_tickets_sold(self) -> int:
        return sum(order.quantity for order in self.orders if order.ticket_type == 'vip')

    @property
    def general_remaining_tickets(self) -> int:
        return max(self.general_capacity - self.general_tickets_sold, 0)

    @property
    def vip_remaining_tickets(self) -> int:
        return max(self.vip_capacity - self.vip_tickets_sold, 0)

    @property
    def total_remaining_tickets(self) -> int:
        return self.general_remaining_tickets + self.vip_remaining_tickets

    @property
    def capacity(self) -> int:
        """Total capacity for backwards compatibility."""
        return self.general_capacity + self.vip_capacity


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
    ticket_type = db.Column(db.String(20), nullable=False, default='general')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    user = db.relationship('User', back_populates='orders')
    event = db.relationship('Event', back_populates='orders')
