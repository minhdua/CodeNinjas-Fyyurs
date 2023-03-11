from datetime import datetime
from enum import Enum
import re
from flask_wtf import Form, FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL, Regexp

from enums import Genre, State


def is_valid_phone(number):
    """ Validate phone numbers like:
    1234567890 - no space
    123.456.7890 - dot separator
    123-456-7890 - dash separator
    123 456 7890 - space separator

    Patterns:
    000 = [0-9]{3}
    0000 = [0-9]{4}
    -.  = ?[-. ]

    Note: (? = optional) - Learn more: https://regex101.com/
    """
    regex = re.compile('^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$')
    return regex.match(number)


class ShowForm(Form):
    artist_id = StringField("artist_id")
    venue_id = StringField("venue_id")
    start_time = DateTimeField("start_time", validators=[
                               DataRequired()], default=datetime.today())


class VenueForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired()],
        choices=State.choices()
    )
    address = StringField("address", validators=[DataRequired()])
    phone = StringField(
        "phone")
    image_link = StringField("image_link")
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired()],
        choices=Genre.choices()
    )
    facebook_link = StringField("facebook_link", validators=[URL()])
    website_link = StringField("website_link")

    seeking_talent = BooleanField("seeking_talent")

    seeking_description = StringField("seeking_description")

    def validate(self, **kwargs):
        # `**kwargs` to match the method's signature in the `FlaskForm` class.
        """Define a custom validate method in your Form:"""
        validated = FlaskForm.validate(self)

        if not validated:
            return False

        if not is_valid_phone(self.phone.data):
            self.phone.errors.append(
                'Invalid phone format (should be xxx-xxx-xxxx).')
            return False

        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append('Invalid genres.')
            return False

        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append('Invalid state.')
            return False

        # if pass validation
        return True


class ArtistForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired()],
        choices=State.choices()
    )
    phone = StringField(
        "phone"
    )
    image_link = StringField("image_link")
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired()],
        choices=Genre.choices()
    )
    facebook_link = StringField(
        "facebook_link",
        validators=[URL()],
    )

    website_link = StringField("website_link")

    seeking_venue = BooleanField("seeking_venue")

    seeking_description = StringField("seeking_description")

    def validate(self, **kwargs):
        # `**kwargs` to match the method's signature in the `FlaskForm` class.
        """Define a custom validate method in your Form:"""
        validated = FlaskForm.validate(self)

        if not validated:
            return False

        if not is_valid_phone(self.phone.data):
            self.phone.errors.append(
                'Invalid phone format (should be xxx-xxx-xxxx).')
            return False

        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append('Invalid genres.')
            return False

        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append('Invalid state.')
            return False

        # if pass validation
        return True
