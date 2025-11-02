# LocalConcerts Project Overview

## Summary
- LocalConcerts is a Flask-based web application that showcases upcoming concerts and allows users to discover, filter, and book events.
- The interface uses Bootstrap 5 with responsive cards, a hero carousel of featured events, and quick-filter buttons for genre, date, and pricing.
- Authenticated users can book General Admission or VIP tickets, manage bookings, and create/update their own events with rich validation.
- Comment threading, flash messaging, and custom error pages ensure a polished and user-friendly experience.
- Seed data (paired with the bundled SQLite DB) provides a realistic catalogue of events with unique imagery and availability.

## Key Features
- Flask blueprints, SQLAlchemy models, and WTForms validation (login/register, event creation, booking, commenting).
- VIP vs General ticket management with separate prices, capacities, and automatic sold-out handling.
- Search bar, genre dropdown, and “Quick Filters” strip with smart status badges.
- Booking history dashboard showing ticket types, prices, and order IDs.
- Dedicated 404 and 500 pages plus collaboration-ready structure.

## Team
- **Jairo Alberto Buitrago Franco** (`main`, `Jairo` branches, maintainer)
- **Faye** (`origin/Faye` branch)
- **Issac** (`origin/Issac` branch)
- **Jonty** (`origin/Jonty` branch)

*(Branch names on GitHub reflect each teammate's contributions.)*
