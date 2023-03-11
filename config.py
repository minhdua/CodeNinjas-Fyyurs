import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Enable debug mode.
DEBUG = os.environ.get('DEBUG') == 'True'

# Connect to the database
SECRET_KEY = os.environ.get('SECRET_KEY')

SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get(
    'SQLALCHEMY_TRACK_MODIFICATIONS') == 'True'
SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO') == 'True'
