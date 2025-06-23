# api/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")

# This is the safeguard we discussed. It will halt the application
# if the connection string is not found in the environment.
if not SUPABASE_CONNECTION_STRING:
    raise ValueError("FATAL ERROR: SUPABASE_CONNECTION_STRING not found. Please set it in your environment or .env file.")

# The SQLAlchemy engine is the starting point for any SQLAlchemy application.
# It provides a source of database connectivity and behavior.
engine = create_engine(SUPABASE_CONNECTION_STRING)

# A SessionLocal class is created. Each instance of SessionLocal will be a
# new database session. This is the primary interface for database operations.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The declarative_base() function returns a class that our ORM models will inherit from.
# This Base class will map our Python objects to database tables.
Base = declarative_base()