#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from sqlalchemy import String, cast, func
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
presentations = db.Table('Shows',
	db.Column('id',db.Integer, primary_key=True),
	db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), nullable=False),
	db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'),nullable=False),
	db.Column('start_time',db.DateTime, nullable=False)
)

class Venue(db.Model):
	__tablename__ = 'Venue'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	city = db.Column(db.String(120))
	state = db.Column(db.String(120))
	address = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	genres = db.Column(db.ARRAY(db.String))
	website = db.Column(db.String(120))
	seeking_talent = db.Column(db.Boolean)
	seeking_description = db.Column(db.String(500))
	artists = db.relationship('Artist', secondary=presentations,
			backref=db.backref('venues', lazy=True))

class Artist(db.Model):
	__tablename__ = 'Artist'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String)
	city = db.Column(db.String(120))
	state = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	image_link = db.Column(db.String(500))
	facebook_link = db.Column(db.String(120))
	website = db.Column(db.String(120))
	genres = db.Column(db.ARRAY(db.String))
	seeking_description = db.Column(db.String(500))
	seeking_venue = db.Column(db.Boolean)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
	date = dateutil.parser.parse(value)
	if format == 'full':
		format="EEEE MMMM, d, y 'at' h:mma"
	elif format == 'medium':
		format="EE MM, dd, y h:mma"
	return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
	return render_template('pages/home.html')


#	Venues
#	----------------------------------------------------------------

@app.route('/venues')
def venues():
	locations = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
	venues_infors = db.session.query(Venue.id, 
							Venue.name, 
							Venue.city,
							Venue.state,
							func.count(presentations.c.id).filter(presentations.c.start_time > datetime.now())
							.label('upcoming_shows')).outerjoin(presentations, presentations.c.venue_id == Venue.id).group_by(Venue.id).all()
	data = []
	for l in locations:
		venues = [v for v in venues_infors if v.city == l.city and v.state == l.state]
		data_formated = {
			"city": l.city,
			"state": l.state,
			"venues": venues
		}
		data.append(data_formated)
	return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
	search_term = request.form.get('search_term', '')
	venues = db.session.query(Venue.id,Venue.name,
				func.count(presentations.c.id).filter(presentations.c.start_time > datetime.now()).label('num_upcoming_shows'))\
				.outerjoin(presentations,presentations.c.venue_id == Venue.id)\
				.filter(Venue.name.ilike(f'%{search_term}%') )\
				.group_by(Venue.id)\
				.all()
	response={
		"count": len(venues),
		"data":venues
	}
	return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
	# shows the venue page with the given venue_id
	venues_all = db.session.query(Venue).all()

	past_shows = db.session.query(presentations.c.artist_id,
								Artist.name.label("artist_name"),
								Artist.image_link.label("artist_image_link"),
								cast(presentations.c.start_time,String).label("start_time"))\
							.join(Artist).filter(presentations.c.venue_id==1)\
							.filter(presentations.c.start_time < datetime.now()).all()
	
	upcoming_shows = db.session.query(presentations.c.artist_id,
								Artist.name.label("artist_name"),
								Artist.image_link.label("artist_image_link"),
								cast(presentations.c.start_time,String).label("start_time"))\
							.join(Artist).filter(presentations.c.venue_id==1)\
							.filter(presentations.c.start_time > datetime.now()).all()
	venues = []
	for v in venues_all:
		venue = {
			"id": v.id,
			"name": v.name,
			"genres": v.genres,
			"address": v.address,
			"city": v.city,
			"state": v.state,
			"phone": v.phone,
			"website": v.website,
			"facebook_link": v.facebook_link,
			"seeking_talent": v.seeking_talent,
			"seeking_description": v.seeking_description,
			"image_link": v.image_link,
			"past_shows": past_shows,
			"upcoming_shows": upcoming_shows,
			"past_shows_count": len(past_shows),
			"upcoming_shows_count": len(upcoming_shows),
		}
		venues.append(venue)
	data = list(filter(lambda d: d['id'] == venue_id, venues))[0]
	return render_template('pages/show_venue.html', venue=data)

#	Create Venue
#	----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
	form = VenueForm()
	return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
	# TODO: insert form data as a new Venue record in the db, instead
	# TODO: modify data to be the data object returned from db insertion

	# on successful db insert, flash success
	flash('Venue ' + request.form['name'] + ' was successfully listed!')
	# TODO: on unsuccessful db insert, flash an error instead.
	# e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
	# see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
	return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
	# TODO: Complete this endpoint for taking a venue_id, and using
	# SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

	# BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
	# clicking that button delete it from the db then redirect the user to the homepage
	return None

#	Artists
#	----------------------------------------------------------------
@app.route('/artists')
def artists():
	data = db.session.query(Artist).all()
	return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
	# TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
	# seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
	# search for "band" should return "The Wild Sax Band".
	search_term = request.form.get('search_term', '')
	artists = db.session.query(Artist.id,Artist.name,
				func.count(presentations.c.id).filter(presentations.c.start_time > datetime.now()).label('num_upcoming_shows'))\
				.outerjoin(presentations,presentations.c.artist_id == Artist.id)\
				.filter(Artist.name.ilike(f'%{search_term}%') )\
				.group_by(Artist.id)\
				.all()
	
	response={
	"count": len(artists),
	"data": artists
	}
	return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
	# shows the artist page with the given artist_id
	all_artist = db.session.query(Artist).all()
	past_shows = db.session.query(presentations.c.venue_id,
					Venue.name.label('venue_name'),
					Venue.image_link.label('venue_image_link'),
					cast(presentations.c.start_time,String).label('start_time'))\
					.join(Venue).filter(presentations.c.artist_id == Artist.id)\
					.filter(presentations.c.start_time < datetime.now()).all()
	upcoming_shows = db.session.query(presentations.c.venue_id,
					Venue.name.label('venue_name'),
					Venue.image_link.label('venue_image_link'),
					cast(presentations.c.start_time,String).label('start_time'))\
					.join(Venue).filter(presentations.c.artist_id == Artist.id)\
					.filter(presentations.c.start_time > datetime.now()).all()
	artists = []
	for a in all_artist:
		artist = {
			"id": a.id,
			"name": a.name,
			"genres": a.genres,
			"city": a.city,
			"state": a.state,
			"phone": a.phone,
			"seeking_venue": a.seeking_venue,
			"image_link": a.image_link,
			"past_shows": past_shows,
			"upcoming_shows": upcoming_shows,
			"past_shows_count": len(past_shows),
			"upcoming_shows_count": len(upcoming_shows),
		}
		artists.append(artist)
	data = list(filter(lambda d: d['id'] == artist_id, artists))[0]
	return render_template('pages/show_artist.html', artist=data)

#	Update
#	----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
	form = ArtistForm()
	artist={
	"id": 4,
	"name": "Guns N Petals",
	"genres": ["Rock n Roll"],
	"city": "San Francisco",
	"state": "CA",
	"phone": "326-123-5000",
	"website": "https://www.gunsnpetalsband.com",
	"facebook_link": "https://www.facebook.com/GunsNPetals",
	"seeking_venue": True,
	"seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
	"image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
	}
	# TODO: populate form with fields from artist with ID <artist_id>
	return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
	# TODO: take values from the form submitted, and update existing
	# artist record with ID <artist_id> using the new attributes

	return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
	form = VenueForm()
	venue={
	"id": 1,
	"name": "The Musical Hop",
	"genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
	"address": "1015 Folsom Street",
	"city": "San Francisco",
	"state": "CA",
	"phone": "123-123-1234",
	"website": "https://www.themusicalhop.com",
	"facebook_link": "https://www.facebook.com/TheMusicalHop",
	"seeking_talent": True,
	"seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
	"image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
	}
	# TODO: populate form with values from venue with ID <venue_id>
	return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
	# TODO: take values from the form submitted, and update existing
	# venue record with ID <venue_id> using the new attributes
	return redirect(url_for('show_venue', venue_id=venue_id))

#	Create Artist
#	----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
	form = ArtistForm()
	return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	# called upon submitting the new artist listing form
	# TODO: insert form data as a new Venue record in the db, instead
	# TODO: modify data to be the data object returned from db insertion

	# on successful db insert, flash success
	flash('Artist ' + request.form['name'] + ' was successfully listed!')
	# TODO: on unsuccessful db insert, flash an error instead.
	# e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
	return render_template('pages/home.html')


#	Shows
#	----------------------------------------------------------------

@app.route('/shows')
def shows():
	# displays list of shows at /shows
	data = db.session.query(presentations.c.venue_id,
						 Venue.name.label('venue_name'),
						 presentations.c.artist_id,
						 Artist.name.label('arist_name'),
						 Artist.image_link.label('artist_image_link'),
						 cast(presentations.c.start_time,String).label('start_time')
							).join(Venue, presentations.c.venue_id == Venue.id).join(Artist, presentations.c.artist_id == Artist.id).all()
	return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
	# renders form. do not touch.
	form = ShowForm()
	return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
	# called to create new shows in the db, upon submitting new show listing form
	# TODO: insert form data as a new Show record in the db, instead

	# on successful db insert, flash success
	flash('Show was successfully listed!')
	# TODO: on unsuccessful db insert, flash an error instead.
	# e.g., flash('An error occurred. Show could not be listed.')
	# see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
	return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
	return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
	return render_template('errors/500.html'), 500


if not app.debug:
	file_handler = FileHandler('error.log')
	file_handler.setFormatter(
		Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
	)
	app.logger.setLevel(logging.INFO)
	file_handler.setLevel(logging.INFO)
	app.logger.addHandler(file_handler)
	app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
	app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)
'''
