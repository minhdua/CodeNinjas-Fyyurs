import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:8Fi1mGBUDYCd@ep-little-band-336241.us-east-2.aws.neon.tech/fyyur?sslmode=require&options=project%3Dpolished-hill-093076"
