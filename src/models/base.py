from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Database URL
# Here, 'sqlite:///example.db' specifies a SQLite database named 'example.db' in the current directory.
# You can change the path to reflect where you want your database file to be stored.
DATABASE_URL = "postgresql://user:password@db/appdb"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
# `scoped_session` is used here to ensure thread safety, which is especially important in web applications
Session = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Session.rollback()
# Base class for your models
Base = declarative_base()


# Optional: function to close database connection cleanly
def shutdown_session(exception=None):
    Session.remove() 