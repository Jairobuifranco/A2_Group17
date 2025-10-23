from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField, DateField, TimeField, DecimalField, SelectField, IntegerField
from wtforms.validators import InputRequired, Length, Email, EqualTo, DataRequired, Length, NumberRange, URL
from datetime import datetime, date

# creates the login information
class LoginForm(FlaskForm):
    user_name=StringField("User Name", validators=[InputRequired('Enter user name')])
    password=PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")

 # this is the registration form
class RegisterForm(FlaskForm):
    user_name=StringField("User Name", validators=[InputRequired()])
    email = StringField("Email Address", validators=[Email("Please enter a valid email")])
    # linking two fields - password should be equal to data entered in confirm
    password=PasswordField("Password", validators=[InputRequired(),
                  EqualTo('confirm', message="Passwords should match")])
    confirm = PasswordField("Confirm Password")

    # submit button
    submit = SubmitField("Register")

# Forms for event creation page
class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    venue = StringField('Venue', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1, max=5000, message='Quantity must be between 1 and 5000')])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=10000, message='Capacity must be between 1 and 10,000')])
    category = SelectField('Category', choices=[
        ('Electronic', 'Electronic' ),
        ('Rock', 'Rock'),
        ('Jazz', 'Jazz'),
        ('Classical', 'Classical'),
        ('Latin', 'Latin')],
        validators=[DataRequired()])
    image_url = StringField('Image Path', [Length(max=255)], default='static/img/hero1.jpg')
    submit = SubmitField('Save Event')

    # Define a function to validate event date must be in the future
    def validate_date(self, field):
        if field.data < date.today():
            from wtforms import ValidationError
            raise ValidationError("Event date must be in the future")
    
     # Define a function to validate event end time must be after start time
    def validate_end_time(self, field):
        if hasattr(self, 'start_time') and self.start_time.data and field.data:
           if field.data <= self.start_time.data:
              from wtforms import ValidationError
              raise ValidationError("End time must be after start time")
    
        
        
        
