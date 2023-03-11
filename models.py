from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


# Initialized without explicit app (Flask instance)
db = SQLAlchemy()


def create_app(app):
    app.config.from_object("config")
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    return db


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), nullable=False)


presentations = db.Table(
    "Shows",
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("artist_id", db.Integer, db.ForeignKey(
        "Artist.id"), nullable=False),
    db.Column("venue_id", db.Integer, db.ForeignKey(
        "Venue.id"), nullable=False),
    db.Column("start_time", db.DateTime, nullable=False),
)


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    shows = db.relationship(
        "Show", backref="Venue", lazy="joined", cascade='all, delete')


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    shows = db.relationship(
        "Show", backref="Artist", lazy="joined", cascade='all, delete')
