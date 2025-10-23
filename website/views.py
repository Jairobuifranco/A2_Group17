from flask import Blueprint, abort, render_template, url_for, flash, request, redirect
from flask_login import login_required, current_user
from datetime import datetime
from .models import db, Event
from .forms import EventForm


# Definitions for Blueprint
main_bp = Blueprint('main', __name__)
events_bp = Blueprint('events', __name__)


@main_bp.route('/')
def index():
    events = db.session.scalars(db.select(Event).order_by(Event.start_time)).all()
    return render_template('index.html', events=events)
    


@main_bp.route('/events/<int:event_id>')
def event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
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

    return render_template('event.html', event=event, event_image_url=resolved_image_url)

# Routes for creating events
# Event details: name, venue, description, date, start time, end time, ticket quantity, capacity, price, category, image
@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    # debugging messages
    print(f"DEBUG: Form submmited: {form.is_submitted()}")
    print(f"DEBUG: Form validated: {form.validate_on_submit()}")
    print(f"DEBUG: Form errors: {form.errors}")

    if form.validate_on_submit():
        
        # Combine date and time into datetime 
        try:
            start_datetime = datetime.combine(form.date.data, form.start_time.data)
            end_datetime = datetime.combine(form.date.data, form.end_time.data)
            
            # Status determination
            status = 'Open'

            # The events completed in the past
            if form.date.data < datetime.today().date():
                status = 'Inactive'
                print(f"DEBUG: Status: {status}")
                # Sold out

            # Image url handling
            image_url_to_save = form.image_url.data if form.image_url.data  else url_for('static', filename='img/hero1.jpg')
            print(f"DEBUG: Image URL: {image_url_to_save}")
        
            # Details needed to create a new event
            new_event = Event (
                title=form.name.data,
                venue=form.venue.data,
                description=form.description.data,
                start_time=start_datetime,
                end_time=end_datetime,
                price=float(form.price.data),
                ticket_quantiy=form.ticket_quantity.data,
                capacity=form.capacity.data,
                category=form.category.data,
                status='Open', # default status
                image_url=image_url_to_save,
                user_id=current_user.id,
            )
            print(f"DEBUG: Event created: {new_event.title}")
            # Save events to database
            db.session.add(new_event)
            db.session.commit()
            print(f"DEBUG: Event saved successfully")
            flash('Event created successfully.', 'success')
            # New events will appear on Home page, Event Details page
            return redirect(url_for('main.index', event_id=new_event.id))
        
        except Exception as e:
         db.session.rollback()
         flash(f'Error event creating: {str(e)}')
  
    return render_template('create.html', form=form, action='Create Event')
        
#  Routes for updating events
@events_bp.route('/update/<int:event_id>', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
        
    # Check user is authorized or not
    if event.user_id != current_user.id:
        flash('You are not authorized to update this event.', 'warning')
        return redirect(url_for('main.index'))
    
    form = EventForm(obj=event)

    # Pre-populate the form with existing data for users to change quickly
    if request.method == 'GET':
        form.name.data = event.title
        form.venue.data = event.venue
        form.description.data = event.description
        form.date.data = event.start_time.date()
        form.start_time.data = event.start_time.time()
        form.end_time.data = event.end_time.time()
        form.price.data = float(event.price)
        form.ticket_quantity.data = event.ticket_quantity
        form.capacity.data = event.capacity
        form.category.data = event.category
        form.image_url.data = event.image_url
        
    if form.validate_on_submit():
        try:
            start_datetime = datetime.combine(form.date.data, form.start_time.data)
            end_datetime = datetime.combine(form.date.data, form.end_time.data)

            event.title=form.name.data
            event.venue=form.venue.data
            event.description=form.description.data
            event.start_time=start_datetime
            event.end_time=end_datetime
            event.price=float(form.price.data)
            event.ticket_quantiy=form.ticket_quantity.data
            event.capacity=form.capacity.data
            event.category=form.category.data
            event.image_url=form.image_url.data if form.image_url.data else event.image_url
            
            # Events happened in the past
            if form.date.data < datetime.today().date():
                event.status = 'Inactive'
            elif event.status == 'Cancelled':
                event.status = 'Cancelled'
            else:
                event.status = 'Open'

            db.session.commit()
            flash('Event updated successfully.', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}')

    return render_template('create.html', form=form, event=event, action='Update Event')

# Route for user to cancel events
@events_bp.route('/cancel/<int:event_id>', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    # Check user is authorized or not
    if event.user_id != current_user.id:
        flash('You are not authorized to cancel this event.', 'warning')
        return redirect(url_for('main.index'))
    try:
        event.status = 'Cancelled'
        db.session.commit()
        flash('Event has been cancelled.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Event can not be cancelled', 'error')
    return redirect(url_for('main.index', event_id=event.id))

        

                
                
            
            





            
     
