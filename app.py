# ----------------------------------------------------------------------------#
# Imports library
# ----------------------------------------------------------------------------#
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request, flash,
    redirect,
    url_for
)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from sqlalchemy import String, cast, func
from forms import *
from models import create_app, db, Venue, Artist, presentations


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
    locations = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()
    venues_infors = (
        db.session.query(
            Venue.id,
            Venue.name,
            Venue.city,
            Venue.state,
            func.count(presentations.c.id).filter(
                presentations.c.start_time > datetime.now()).label("upcoming_shows"),
        )
        .outerjoin(presentations, presentations.c.venue_id == Venue.id)
        .group_by(Venue.id)
        .all()
    )
    data = []
    for l in locations:
        venues = [v for v in venues_infors if v.city ==
                  l.city and v.state == l.state]
        data_formated = {"city": l.city, "state": l.state, "venues": venues}
        data.append(data_formated)
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    venues = (
        db.session.query(
            Venue.id,
            Venue.name,
            func.count(presentations.c.id)
            .filter(presentations.c.start_time > datetime.now())
            .label("num_upcoming_shows"),
        )
        .outerjoin(presentations, presentations.c.venue_id == Venue.id)
        .filter(Venue.name.ilike(f"%{search_term}%"))
        .group_by(Venue.id)
        .all()
    )
    response = {"count": len(venues), "data": venues}
    return render_template("pages/search_venues.html", results=response, search_term=search_term)


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = db.session.get(Venue, venue_id)
    if not venue:
        return render_template('errors/object_not_found.html', object_name="Venue")

    _shows = (db.session.query(
        presentations.c.artist_id,
        Artist.name.label("artist_name"),
        Artist.image_link.label("artist_image_link"),
        presentations.c.start_time.label("_start_time"),
        cast(presentations.c.start_time, String).label("start_time")
    )
        .join(Artist)
        .filter(presentations.c.venue_id == venue.id)
        .all())

    past_shows = [s for s in _shows if s._start_time < datetime.now()]
    upcoming_shows = [s for s in _shows if s._start_time > datetime.now()]

    venue.past_shows = past_shows
    venue.upcoming_shows = upcoming_shows
    setattr(venue, "past_shows_count", len(past_shows))
    setattr(venue, "upcoming_shows_count", len(upcoming_shows))

    return render_template("pages/show_venue.html", venue=venue)

# 	Create Venue
# 	----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        venue = Venue(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            address=request.form["address"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            image_link=request.form["image_link"],
            facebook_link=request.form["facebook_link"],
            website=request.form["website_link"],
            seeking_talent=True if "seeking_talent" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(venue)
        db.session.commit()
        flash("Venue " + request.form["name"] +
              " was successfully listed!")
    except Exception as ex:
        print(ex)
        db.session.rollback()
        flash("An error occurred. Venue " +
              request.form["name"] + " could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        venue = db.session.get(Venue, venue_id)
        if not venue:
            return render_template('errors/object_not_found.html', object_name="Venue")

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
    data = db.session.query(Artist).all()
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    artists = (
        db.session.query(
            Artist.id,
            Artist.name,
            func.count(presentations.c.id)
            .filter(presentations.c.start_time > datetime.now())
            .label("num_upcoming_shows"),
        )
        .outerjoin(presentations, presentations.c.artist_id == Artist.id)
        .filter(Artist.name.ilike(f"%{search_term}%"))
        .group_by(Artist.id)
        .all()
    )

    response = {"count": len(artists), "data": artists}
    return render_template("pages/search_artists.html", results=response, search_term=search_term)


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = db.session.get(Artist, artist_id)
    if not artist:
        return render_template('errors/object_not_found.html', object_name="Artist")

    _shows = (db.session.query(
        presentations.c.venue_id,
        Venue.name.label("venue_name"),
        Venue.image_link.label("venue_image_link"),
        presentations.c.start_time.label("_start_time"),
        cast(presentations.c.start_time, String).label("start_time"),
    )
        .join(Venue)
        .filter(presentations.c.artist_id == Artist.id)
        .all())

    past_shows = [s for s in _shows if s._start_time < datetime.now()]
    upcoming_shows = [s for s in _shows if s._start_time > datetime.now()]

    artist.past_shows = past_shows
    artist.upcoming_shows = upcoming_shows
    setattr(artist, "past_shows_count", len(past_shows))
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template("pages/show_artist.html", artist=artist)

# 	Update
# 	----------------------------------------------------------------


@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).get(artist_id)
    if not artist:
        return render_template('errors/object_not_found.html', object_name="Artist")

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
    artist = db.session.query(Artist).get(artist_id)
    if not artist:
        return render_template('errors/object_not_found.html', object_name="Artist")

    artist.name = request.form["name"]
    artist.genres = request.form.getlist("genres")
    artist.city = request.form["city"]
    artist.state = request.form["state"]
    artist.phone = request.form["phone"]
    artist.website = request.form["website_link"]
    artist.facebook_link = request.form["facebook_link"]
    artist.seeking_venue = True if request.form.get(
        "seeking_venue") else False
    artist.seeking_description = request.form["seeking_description"]
    artist.image_link = request.form["image_link"]

    db.session.commit()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = db.session.query(Venue).get(venue_id)

    if not venue:
        return render_template('errors/object_not_found.html', object_name="Venue")

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
    venue = db.session.query(Venue).get(venue_id)
    if not venue:
        return render_template('errors/object_not_found.html', object_name="Venue")

    venue.name = request.form["name"]
    venue.genres = request.form.getlist("genres")
    venue.address = request.form["address"]
    venue.city = request.form["city"]
    venue.state = request.form["state"]
    venue.phone = request.form["phone"]
    venue.website = request.form["website_link"]
    venue.facebook_link = request.form["facebook_link"]
    venue.seeking_talent = True if request.form.get(
        "seeking_talent") else False
    venue.seeking_description = request.form["seeking_description"]
    venue.image_link = request.form["image_link"]

    db.session.commit()
    return redirect(url_for("show_venue", venue_id=venue_id))

# 	Create Artist
# 	----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        artist = Artist(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            facebook_link=request.form["facebook_link"],
            image_link=request.form["image_link"],
            website=request.form["website_link"],
            seeking_venue=True if "seeking_venue" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] +
              " was successfully listed!")
    except Exception as ex:
        print(ex)
        db.session.rollback()
        flash("An error occurred. Artist " +
              request.form["name"] + " could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")

# 	Shows
# 	----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    data = (
        db.session.query(
            presentations.c.venue_id,
            Venue.name.label("venue_name"),
            presentations.c.artist_id,
            Artist.name.label("arist_name"),
            Artist.image_link.label("artist_image_link"),
            cast(presentations.c.start_time, String).label("start_time"),
        )
        .join(Venue, presentations.c.venue_id == Venue.id)
        .join(Artist, presentations.c.artist_id == Artist.id)
        .all()
    )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create", methods=["GET"])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    print("request", request.form)
    try:
        presents = presentations.insert().values(
            artist_id=request.form["artist_id"],
            venue_id=request.form["venue_id"],
            start_time=request.form["start_time"],
        )
        db.session.execute(presents)
        db.session.commit()
        flash("Show was successfully listed!")
    except Exception as ex:
        print(ex)
        db.session.rollback()
        flash("Show was failed listed!")
    finally:
        db.session.close()
    return render_template("pages/home.html")


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
