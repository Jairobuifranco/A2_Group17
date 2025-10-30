from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField, DateField, TimeField, DecimalField, SelectField, IntegerField, FileField
from wtforms.validators import InputRequired, Length, Email, EqualTo, DataRequired, Length, NumberRange, ValidationError
from datetime import date
from flask_wtf.file import FileRequired, FileAllowed

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

# Create Event form #
class EventForm(FlaskForm):
    # Add the types of files allowed as a set #
    ALLOWED_FILE = {'jpg','jpeg','png','gif'}
    name = StringField('Event Name', validators=[DataRequired(), Length(max=25)])
    venue = StringField('Venue', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0, message='Price can not be negative')])
    ticket_quantity = IntegerField('Ticket Quantity', validators=[DataRequired(), NumberRange(min=1, max=5000, message='Quantity must be between 1 and 5000')])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=10000, message='Capacity must be between 1 and 10,000')])
    category = SelectField('Category', choices=[
        ('Electronic', 'Electronic' ),
        ('Rock', 'Rock'),
        ('Jazz', 'Jazz'),
        ('Classical', 'Classical'),
        ('Latin', 'Latin')],
        validators=[DataRequired()])
    
    # Image handling: file upload or url #
    image_file = FileField('Event Image', validators=[FileAllowed(ALLOWED_FILE, message='Only jpg, jpeg, png, gif are supported')])

    image_url = StringField('Or Image URL', [Length(max=255)], description='Alternative: You can also enter image url')
    submit = SubmitField('Create Event')
   

    # Define a function to validate event date must be in the future #
    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError("Event date must be in the future")
    
    # Define a function to validate event end time must be after start time #
    def validate_end_time(self, field):
        if hasattr(self, 'start_time') and self.start_time.data and field.data:
           if field.data <= self.start_time.data:
              raise ValidationError("End time must be after start time")
    
        
        
        
