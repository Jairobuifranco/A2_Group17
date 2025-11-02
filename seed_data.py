"""Populate the local SQLite database with example events and comments."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from werkzeug.security import generate_password_hash

from website import create_app, db
from website.models import Comment, Event, Order, User


def seed() -> None:
    # Populate the SQLite database with exemplar users, events, and bookings.
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
                first_name="Alex",
                last_name="Rivera",
                email="alex@example.com",
                password_hash=generate_password_hash("Password123!"),
                contact_number="0400 111 222",
                street_address="123 Music Lane, Brisbane",
            ),
            "sam": User(
                first_name="Sam",
                last_name="Chen",
                email="sam@example.com",
                password_hash=generate_password_hash("Password123!"),
                contact_number="0400 333 444",
                street_address="89 Riverfront Ave, Brisbane",
            ),
            "maria": User(
                first_name="Maria",
                last_name="Lopez",
                email="maria@example.com",
                password_hash=generate_password_hash("Password123!"),
                contact_number="0400 555 666",
                street_address="45 Festival Rd, Brisbane",
            ),
            "liam": User(
                first_name="Liam",
                last_name="O'Connor",
                email="liam@example.com",
                password_hash=generate_password_hash("Password123!"),
                contact_number="0400 777 111",
                street_address="12 Valley View, Brisbane",
            ),
            "sienna": User(
                first_name="Sienna",
                last_name="Chambers",
                email="sienna@example.com",
                password_hash=generate_password_hash("Password123!"),
                contact_number="0400 999 333",
                street_address="77 Harbour Lane, Brisbane",
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
                start_time=base_date + timedelta(days=1, hours=19 - base_date.hour),
                end_time=base_date + timedelta(days=1, hours=23 - base_date.hour),
                general_price=Decimal("39.00"),
                vip_price=Decimal("79.00"),
                status="Open",
                category="Festival",
                image_url="img/hero1.jpg",
                owner=users["alex"],
                general_capacity=160,
                vip_capacity=40,
            ),
            Event(
                title="Jazz Under Stars",
                venue="New Farm Park",
                description="Smooth jazz ensembles with a relaxed picnic vibe by the river.",
                start_time=base_date + timedelta(days=10, hours=18 - base_date.hour),
                end_time=base_date + timedelta(days=10, hours=21 - base_date.hour),
                general_price=Decimal("25.00"),
                vip_price=Decimal("55.00"),
                status="Open",
                category="Jazz",
                image_url="img/jazz.jpg",
                owner=users["sam"],
                general_capacity=110,
                vip_capacity=20,
            ),
            Event(
                title="Symphony Night",
                venue="QPAC Concert Hall",
                description="A full orchestral program celebrating modern film scores.",
                start_time=base_date + timedelta(days=14, hours=20 - base_date.hour),
                end_time=base_date + timedelta(days=14, hours=22 - base_date.hour),
                general_price=Decimal("65.00"),
                vip_price=Decimal("120.00"),
                status="Sold Out",
                category="Classical",
                image_url="img/classical1.jpg",
                owner=users["maria"],
                general_capacity=2,
                vip_capacity=2,
            ),
            Event(
                title="Street Hip Hop Showdown",
                venue="Fortitude Music Hall",
                description="Queensland's best crews battle it out with live DJs and guest MCs.",
                start_time=base_date + timedelta(days=3, hours=20 - base_date.hour),
                end_time=base_date + timedelta(days=3, hours=23 - base_date.hour),
                general_price=Decimal("20.00"),
                vip_price=Decimal("45.00"),
                status="Open",
                category="Hip Hop",
                image_url="img/indie.jpg",
                owner=users["alex"],
                general_capacity=180,
                vip_capacity=30,
            ),
            Event(
                title="Laneway Indie Sessions",
                venue="The Brightside",
                description="An intimate evening with emerging indie artists and acoustic sets.",
                start_time=base_date + timedelta(days=5, hours=19 - base_date.hour),
                end_time=base_date + timedelta(days=5, hours=22 - base_date.hour),
                general_price=Decimal("34.00"),
                vip_price=Decimal("68.00"),
                status="Inactive",
                category="Rock",
                image_url="img/rock.jpg",
                owner=users["sam"],
                general_capacity=80,
                vip_capacity=18,
            ),
            Event(
                title="Retro Vinyl Fair",
                venue="Brisbane Powerhouse",
                description="Collectors and DJs unite for a day of rare vinyl finds, workshops, and listening lounges.",
                start_time=base_date + timedelta(days=5, hours=11 - base_date.hour),
                end_time=base_date + timedelta(days=5, hours=17 - base_date.hour),
                general_price=Decimal("15.00"),
                vip_price=None,
                status="Cancelled",
                category="Other",
                image_url="img/concert.jpg",
                owner=users["maria"],
                general_capacity=150,
                vip_capacity=0,
            ),
            Event(
                title="Sunset Acoustic Picnic",
                venue="Kangaroo Point Cliffs Park",
                description="Bring a blanket for relaxing acoustic sets as the sun dips behind the skyline.",
                start_time=base_date + timedelta(days=4, hours=18 - base_date.hour),
                end_time=base_date + timedelta(days=4, hours=21 - base_date.hour),
                general_price=Decimal("22.00"),
                vip_price=Decimal("48.00"),
                status="Open",
                category="Other",
                image_url="img/latin.jpg",
                owner=users["liam"],
                general_capacity=140,
                vip_capacity=25,
            ),
            Event(
                title="Electronic Night Market",
                venue="South Bank Piazza",
                description="Immersive electronica with pop-up food vendors, art stalls, and live VJ sets.",
                start_time=base_date + timedelta(days=2, hours=19 - base_date.hour),
                end_time=base_date + timedelta(days=2, hours=23 - base_date.hour),
                general_price=Decimal("45.00"),
                vip_price=Decimal("85.00"),
                status="Open",
                category="Electronic",
                image_url="img/hero2.jpg",
                owner=users["sam"],
                general_capacity=220,
                vip_capacity=60,
            ),
            Event(
                title="Community Choir Gala",
                venue="City Hall Auditorium",
                description="A heart-warming evening featuring Brisbane's best community choirs in harmony.",
                start_time=base_date + timedelta(days=12, hours=18 - base_date.hour),
                end_time=base_date + timedelta(days=12, hours=20 - base_date.hour),
                general_price=Decimal("19.00"),
                vip_price=Decimal("38.00"),
                status="Open",
                category="Classical",
                image_url="img/symphony.jpg",
                owner=users["sienna"],
                general_capacity=160,
                vip_capacity=35,
            ),
            Event(
                title="Indie Rooftop Sessions",
                venue="Howard Smith Wharves",
                description="Discover rising indie bands on a breezy riverside rooftop with craft beverages.",
                start_time=base_date + timedelta(days=6, hours=20 - base_date.hour),
                end_time=base_date + timedelta(days=6, hours=23 - base_date.hour),
                general_price=Decimal("35.00"),
                vip_price=Decimal("70.00"),
                status="Open",
                category="Rock",
                image_url="img/concert1.jpg",
                owner=users["sienna"],
                general_capacity=130,
                vip_capacity=20,
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
            Comment(
                body="That laneway lighting makes the sets feel magical.",
                created_at=events[4].start_time - timedelta(days=1),
                user=users["sam"],
                event=events[4],
            ),
            Comment(
                body="Hoping this fair is rescheduled soon!",
                created_at=events[5].start_time - timedelta(hours=6),
                user=users["maria"],
                event=events[5],
            ),
            Comment(
                body="Booked a VIP picnic pass—can't wait for the skyline views!",
                created_at=events[6].start_time - timedelta(days=2, hours=3),
                user=users["sienna"],
                event=events[6],
            ),
            Comment(
                body="Line-up looks fire, bringing the crew!",
                created_at=events[7].start_time - timedelta(days=1, hours=2),
                user=users["alex"],
                event=events[7],
            ),
            Comment(
                body="Our choir students are so excited to perform here!",
                created_at=events[8].start_time - timedelta(days=5),
                user=users["liam"],
                event=events[8],
            ),
            Comment(
                body="Any recommendations for parking nearby?",
                created_at=events[9].start_time - timedelta(days=2, hours=4),
                user=users["sam"],
                event=events[9],
            ),
        ]

        db.session.add_all(comments)

        orders: list[Order] = [
            Order(user=users["alex"], event=events[0], quantity=2, ticket_type="general"),
            Order(user=users["alex"], event=events[3], quantity=1, ticket_type="vip"),
            Order(user=users["sam"], event=events[1], quantity=4, ticket_type="general"),
            Order(user=users["maria"], event=events[2], quantity=2, ticket_type="general"),
            Order(user=users["alex"], event=events[4], quantity=3, ticket_type="general"),
            Order(user=users["sam"], event=events[4], quantity=2, ticket_type="vip"),
            Order(user=users["maria"], event=events[2], quantity=2, ticket_type="vip"),
            Order(user=users["liam"], event=events[6], quantity=2, ticket_type="vip"),
            Order(user=users["sienna"], event=events[7], quantity=5, ticket_type="general"),
            Order(user=users["alex"], event=events[7], quantity=2, ticket_type="vip"),
            Order(user=users["sam"], event=events[8], quantity=3, ticket_type="general"),
            Order(user=users["maria"], event=events[8], quantity=2, ticket_type="vip"),
            Order(user=users["sienna"], event=events[9], quantity=4, ticket_type="general"),
        ]

        db.session.add_all(orders)
        db.session.commit()

        print(
            f"Inserted {len(events)} events, {len(users)} users, {len(comments)} comments, "
            f"and {len(orders)} orders."
        )


if __name__ == "__main__":
    seed()
