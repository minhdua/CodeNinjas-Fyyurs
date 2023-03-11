# ----------------------------------------------------------------------------#
# Imports library
# ----------------------------------------------------------------------------#
from datetime import datetime
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request, flash,
    redirect,
    url_for
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from sqlalchemy import String, cast, func
from forms import *
from models import create_app, Venue, Artist, Show


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
db = create_app(app)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


# 	Venues
# 	----------------------------------------------------------------
@app.route("/venues")
def venues():
    locations = Venue.query.distinct(Venue.city, Venue.state).all()
    venues = Venue.query.all()
    data = []
    for l in locations:
        data.append({
            "city": l.city,
            "state": l.state,
            "venues": [
                {
                    "id": v.id,
                    "name": v.name,
                    "upcoming_shows": len([s for s in v.shows if s.start_time > datetime.now()])
                } for v in venues if v.city == l.city and v.state == l.state
            ]
        })
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    response = {
        "count": len(venues),
        "data": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len([s for s in venue.shows if s.start_time > datetime.now()])
        } for venue in venues]
    }
    return render_template("pages/search_venues.html", results=response, search_term=search_term)


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get_or_404(venue_id)

    upcoming_shows = []
    past_shows = []
    for s in venue.shows:
        show = {
            "artist_id": s.artist_id,
            "artist_name": s.Artist.name,
            "artist_image_link": s.Artist.image_link,
            "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M"),
        }
        if (s.start_time > datetime.now()):
            upcoming_shows.append(show)
        else:
            past_shows.append(show)

    data = vars(venue)
    data["upcoming_shows"] = upcoming_shows
    data["past_shows"] = past_shows
    data["upcoming_shows_count"] = len(upcoming_shows)
    data["past_shows_count"] = len(past_shows)

    return render_template("pages/show_venue.html", venue=data)

# 	Create Venue
# 	----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # Set the FlaskForm
    form = VenueForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except ValueError as e:
            print(e)
            db.session.rollback()
            flash("An error occurred. Venue " +
                  request.form["name"] + " could not be listed.")
        finally:
            db.session.close()

        return render_template("pages/home.html")
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(f"{field}: {error}")
        flash('Please fix the following errors: ' + ', '.join(message))
        return render_template('forms/new_venue.html', form=form)


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get_or_404(venue_id)

    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form, meta={'csrf': False})
    venue = Venue.query.get_or_404(venue_id)
    if form.validate():
        try:
            venue.name = form.name.data
            venue.genres = form.genres.data
            venue.address = form.address.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.phone = form.phone.data
            venue.website = form.website_link.data
            venue.facebook_link = form.facebook_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.image_link = form.image_link.data
            flash(f'Venue {request.form["name"]} was successfully updated!')
            db.session.commit()
        except Exception as ex:
            flash(f'An error occurred. Venue {venue_id} could not be updated.')
            print(ex)
            db.session.rollback()
        finally:
            db.session.close()
        return redirect(url_for("show_venue", venue_id=venue_id))
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(f"{field}: {error}")
        flash('Please fix the following errors: ' + ', '.join(message))
        return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get_or_404(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as ex:
        flash("An error occurred. Venue " +
              venue_id + " could not be deleted.")
        print(ex)
        db.session.rollback()
    finally:
        db.session.close()
    return render_template("pages/home.html")

# 	Artists
# 	----------------------------------------------------------------


@app.route("/artists")
def artists():
    data = Artist.query.all()
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():

    search_term = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {"count": len(artists),
                "data": [{
                    "id": artist.id,
                    "name": artist.name,
                    "num_upcoming_shows": len([s for s in artist.shows if s.start_time > datetime.now()])
                } for artist in artists]}
    return render_template("pages/search_artists.html", results=response, search_term=search_term)


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get_or_404(artist_id)

    upcoming_shows = []
    past_shows = []
    for s in artist.shows:
        show = {
            "venue_id": s.venue_id,
            "venue_name": s.Venue.name,
            "venue_image_link": s.Venue.image_link,
            "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M"),
        }
        if (s.start_time > datetime.now()):
            upcoming_shows.append(show)
        else:
            past_shows.append(show)

    data = vars(artist)
    data["upcoming_shows"] = upcoming_shows
    data["past_shows"] = past_shows
    data["upcoming_shows_count"] = len(upcoming_shows)
    data["past_shows_count"] = len(past_shows)
    return render_template("pages/show_artist.html", artist=artist)

# 	Update
# 	----------------------------------------------------------------


@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get_or_404(artist_id)

    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):

    form = ArtistForm(request.form, meta={'csrf': False})
    artist = Artist.query.get_or_404(artist_id)
    if form.validate():
        try:
            artist.name = form.name.data
            artist.genres = form.genres.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.website = form.website_link.data
            artist.facebook_link = form.facebook_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.image_link = form.image_link.data
            flash(f'Artist {request.form["name"]} was successfully updated!')
            db.session.commit()
        except Exception as ex:
            flash(
                f'An error occurred. Artist {artist_id} could not be updated.')
            print(ex)
            db.session.rollback()
        finally:
            db.session.close()
        return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(f"{field}: {error}")
        flash('Please fix the following errors: ' + ', '.join(message))
        return render_template('forms/edit_artist.html', form=form, artist=artist)

# 	Create Artist
# 	----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # Set the FlaskForm
    form = ArtistForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )
            db.session.add(artist)
            db.session.commit()
            flash(f'Artist {request.form["name"]} was successfully listed!')
        except ValueError as e:
            print(e)
            db.session.rollback()
            flash("An error occurred. Venue " +
                  request.form["name"] + " could not be listed.")
        finally:
            db.session.close()
        return render_template("pages/home.html")
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(f"{field}: {error}")
        flash('Please fix the following errors: ' + ', '.join(message))
        return render_template('forms/new_artist.html', form=form)

# 	Shows
# 	----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    shows = Show.query.all()
    data = [{
        "venue_id": show.venue_id,
        "venue_name": show.Venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.Artist.name,
        "artist_image_link": show.Artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for show in shows]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create", methods=["GET"])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # Set the FlaskForm
    form = ShowForm(request.form, meta={'csrf': False})
    # Validate all fields
    if form.validate():
        try:
            show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data,
            )
            db.session.add(show)
            db.session.commit()
            flash(f'Show was successfully listed!')
        except ValueError as e:
            print(e)
            db.session.rollback()
            flash("An error occurred. Show could not be listed.")
        finally:
            db.session.close()
        return render_template("pages/home.html")
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(f"{field}: {error}")
        flash('Please fix the following errors: ' + ', '.join(message))
        return render_template('forms/new_artist.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#


# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
"""
