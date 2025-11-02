"""Populate the local SQLite database with example events and comments."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from werkzeug.security import generate_password_hash

from website import create_app, db
from website.models import Comment, Event, Order, User


def seed() -> None:
    """Insert sample users, events, and comments if the database is empty."""
    app = create_app()
    with app.app_context():
        db.create_all()

        existing_event = db.session.scalar(db.select(Event.id).limit(1))
        if existing_event:
            print("Database already contains events; skipping seeding.")
            return

        users: dict[str, User] = {
            "alex": User(
                name="Alex",
                email="alex@example.com",
                password_hash=generate_password_hash("Password123!"),
                phone="+61 412 345 678",
                street_address="123 Main St, Brisbane City QLD 4000"
            ),
            "sam": User(
                name="Sam",
                email="sam@example.com",
                password_hash=generate_password_hash("Password123!"),
                phone="+61 434 567 890",
                street_address="789 Sam Street, Brisbane City QLD 4000"
            ),
            "maria": User(
                name="Maria",
                email="maria@example.com",
                password_hash=generate_password_hash("Password123!"),
                phone="+61 432 678 945",
                street_address="780 Maria Street, Brisbane City QLD 4000"
            ),
        }
        db.session.add_all(users.values())
        db.session.flush()

        base_date = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        events: list[Event] = [
            Event(
                title="City Lights Festival",
                venue="Riverstage",
                description=(
                    "A night of upbeat indie and pop performances under the stars "
                    "with food trucks and art installations."
                ),
                start_time=base_date + timedelta(days=7, hours=19 - base_date.hour),
                end_time=base_date + timedelta(days=7, hours=23 - base_date.hour),
                general_price=Decimal("39.00"),
                general_tickets=500,
                vip_price=Decimal("59.00"),
                vip_tickets=300,
                status="Open",
                category="Festival",
                image_url="img/hero1.jpg",
            ),
            Event(
                title="Jazz Under Stars",
                venue="New Farm Park",
                description="Smooth jazz ensembles with a relaxed picnic vibe by the river.",
                start_time=base_date + timedelta(days=10, hours=18 - base_date.hour),
                end_time=base_date + timedelta(days=10, hours=21 - base_date.hour),
                general_price=Decimal("59.00"),
                general_tickets=500,
                vip_price=Decimal("89.00"),
                vip_tickets=300,
                status="Open",
                category="Jazz",
                image_url="img/jazz.jpg",
            ),
            Event(
                title="Symphony Night",
                venue="QPAC Concert Hall",
                description="A full orchestral program celebrating modern film scores.",
                start_time=base_date + timedelta(days=14, hours=20 - base_date.hour),
                end_time=base_date + timedelta(days=14, hours=22 - base_date.hour),
                general_price=Decimal("30.00"),
                general_tickets=500,
                vip_price=Decimal("60.00"),
                vip_tickets=300,
                status="Sold Out",
                category="Classical",
                image_url="img/symphony.jpg",
            ),
            Event(
                title="Street Hip Hop Showdown",
                venue="Fortitude Music Hall",
                description="Queensland's best crews battle it out with live DJs and guest MCs.",
                start_time=base_date + timedelta(days=3, hours=20 - base_date.hour),
                end_time=base_date + timedelta(days=3, hours=23 - base_date.hour),
                general_price=Decimal("50.00"),
                general_tickets=500,
                vip_price=Decimal("75.00"),
                vip_tickets=300,
                status="Open",
                category="Hip Hop",
                image_url="img/hiphop.jpg",
            ),
        ]

        db.session.add_all(events)
        db.session.flush()

        comments: list[Comment] = [
            Comment(
                body="Loved last year's energy — can't wait!",
                created_at=events[0].start_time - timedelta(days=2),
                user=users["alex"],
                event=events[0],
            ),
            Comment(
                body="Do they allow BYO picnic blankets?",
                created_at=events[0].start_time - timedelta(days=1, hours=5),
                user=users["sam"],
                event=events[0],
            ),
            Comment(
                body="Bringing the whole family — see you there!",
                created_at=events[1].start_time - timedelta(days=3),
                user=users["maria"],
                event=events[1],
            ),
            Comment(
                body="Will there be an encore of the Star Wars suite?",
                created_at=events[2].start_time - timedelta(days=4),
                user=users["sam"],
                event=events[2],
            ),
            Comment(
                body="Crew practice has us hyped for this lineup!",
                created_at=events[3].start_time - timedelta(days=1, hours=3),
                user=users["alex"],
                event=events[3],
            ),
        ]

        db.session.add_all(comments)

        orders: list[Order] = [
            Order(user=users["alex"], event=events[0], quantity=2),
            Order(user=users["alex"], event=events[3], quantity=1),
            Order(user=users["sam"], event=events[1], quantity=4),
            Order(user=users["maria"], event=events[2], quantity=2),
        ]

        db.session.add_all(orders)
        db.session.commit()

        print(
            f"Inserted {len(events)} events, {len(users)} users, {len(comments)} comments, "
            f"and {len(orders)} orders."
        )


if __name__ == "__main__":
    seed()
