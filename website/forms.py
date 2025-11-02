from datetime import date

from flask_wtf import FlaskForm
from wtforms.fields import (
    DateField,
    DecimalField,
    EmailField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
    PasswordField,
)
from wtforms.validators import Email, EqualTo, InputRequired, Length, NumberRange, Optional, ValidationError


EVENT_CATEGORY_OPTIONS = [
    "Electronic",
    "Rock",
    "Jazz",
    "Classical",
    "Latin",
    "Hip Hop",
    "Festival",
    "Other",
]


# creates the login information
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired('Enter email'), Email()])
    password = PasswordField("Password", validators=[InputRequired('Enter password')])
    submit = SubmitField("Log in")


# this is the registration form
class RegisterForm(FlaskForm):
    first_name = StringField("First Name", validators=[InputRequired(), Length(max=80)])
    last_name = StringField("Surname", validators=[InputRequired(), Length(max=80)])
    email = EmailField("Email Address", validators=[InputRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Password",
        validators=[InputRequired(), EqualTo('confirm', message="Passwords should match")],
    )
    confirm = PasswordField("Confirm Password")
    contact_number = StringField("Contact Number", validators=[InputRequired(), Length(max=30)])
    street_address = StringField("Street Address", validators=[InputRequired(), Length(max=255)])

    # submit button
    submit = SubmitField("Create Account")


class EventForm(FlaskForm):
    title = StringField("Event Name", validators=[InputRequired(), Length(max=150)])
    venue = StringField("Venue", validators=[InputRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[InputRequired(), Length(max=1000)])
    start_date = DateField("Date", format='%Y-%m-%d', validators=[InputRequired()])
    start_time = TimeField("Start Time", validators=[InputRequired()])
    end_time = TimeField("End Time", validators=[InputRequired()])
    general_price = DecimalField(
        "General Admission Price (AUD)",
        places=2,
        rounding=None,
        validators=[InputRequired(), NumberRange(min=0)],
    )
    vip_price = DecimalField(
        "VIP Price (AUD)",
        places=2,
        rounding=None,
        validators=[Optional(), NumberRange(min=0)],
    )
    category = SelectField(
        "Category",
        choices=[(category, category) for category in EVENT_CATEGORY_OPTIONS],
        validators=[InputRequired()],
    )
    general_capacity = IntegerField(
        "General Admission Tickets",
        validators=[InputRequired(), NumberRange(min=0, message="General admission tickets must be zero or more.")],
    )
    vip_capacity = IntegerField(
        "VIP Tickets",
        validators=[InputRequired(), NumberRange(min=0, message="VIP tickets must be zero or more.")],
    )
    image_url = StringField("Image URL", validators=[InputRequired(), Length(max=255)])
    submit = SubmitField("Save Event")

    def validate_start_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError("Event date must be today or in the future.")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if (self.general_capacity.data or 0) <= 0 and (self.vip_capacity.data or 0) <= 0:
            self.general_capacity.errors.append("Provide at least one ticket for general admission or VIP.")
            self.vip_capacity.errors.append("Provide at least one ticket for general admission or VIP.")
            return False

        if (self.vip_capacity.data or 0) > 0 and (self.vip_price.data is None):
            self.vip_price.errors.append("Provide a VIP price when allocating VIP tickets.")
            return False

        return True


class BookingForm(FlaskForm):
    ticket_type = SelectField(
        "Ticket Type",
        choices=[("general", "General Admission"), ("vip", "VIP")],
        validators=[InputRequired()],
    )
    quantity = SelectField(
        "Tickets",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8")],
        coerce=int,
        validators=[InputRequired()],
    )
    submit = SubmitField("Book Now")


class CommentForm(FlaskForm):
    body = TextAreaField(
        "Comment",
        validators=[
            InputRequired("Comment cannot be empty"),
            Length(max=500, message="Comments must be 500 characters or fewer."),
        ],
    )
    submit = SubmitField("Post Comment")
