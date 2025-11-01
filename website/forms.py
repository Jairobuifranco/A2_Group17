from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
    PasswordField,
)
from wtforms.validators import Email, EqualTo, InputRequired, Length, NumberRange


# creates the login information
class LoginForm(FlaskForm):
    user_name = StringField("User Name", validators=[InputRequired('Enter user name')])
    password = PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")


# this is the registration form
class RegisterForm(FlaskForm):
    user_name = StringField("User Name", validators=[InputRequired(), Length(max=80)])
    email = StringField("Email Address", validators=[Email("Please enter a valid email"), Length(max=120)])
    phone = StringField("Phone Number", validators=[Length(max=20, message="Phone number too long")])
    street_address = StringField("Street Address", validators=[Length(max=255, message="Address too long")])

    # linking two fields - password should be equal to data entered in confirm
    password = PasswordField(
        "Password",
        validators=[InputRequired(), EqualTo('confirm', message="Passwords should match")],
    )
    confirm = PasswordField("Confirm Password")

    # submit button
    submit = SubmitField("Register")


class EventForm(FlaskForm):
    title = StringField("Event Name", validators=[InputRequired(), Length(max=150)])
    venue = StringField("Venue", validators=[InputRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[InputRequired(), Length(max=1000)])
    start_date = DateField("Date", format='%Y-%m-%d', validators=[InputRequired()])
    start_time = TimeField("Start Time", validators=[InputRequired()])
    end_time = TimeField("End Time", validators=[InputRequired()])
    price = DecimalField(
        "Price (AUD)",
        places=2,
        rounding=None,
        validators=[InputRequired(), NumberRange(min=0)],
    )
    category = SelectField(
        "Category",
        choices=[
            ("Electronic", "Electronic"),
            ("Rock", "Rock"),
            ("Jazz", "Jazz"),
            ("Classical", "Classical"),
            ("Latin", "Latin"),
            ("Hip Hop", "Hip Hop"),
            ("Other", "Other"),
        ],
        validators=[InputRequired()],
    )
    status = SelectField(
        "Status",
        choices=[
            ("Open", "Open"),
            ("Inactive", "Inactive"),
            ("Sold Out", "Sold Out"),
            ("Cancelled", "Cancelled"),
        ],
        validators=[InputRequired()],
    )
    image_url = StringField("Image URL", validators=[InputRequired(), Length(max=255)])
    submit = SubmitField("Save Event")


class BookingForm(FlaskForm):
    quantity = SelectField(
        "Tickets",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8")],
        coerce=int,
        validators=[InputRequired()],
    )
    submit = SubmitField("Book Now")
