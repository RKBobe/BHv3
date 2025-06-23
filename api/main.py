# api/main.py

from fastapi import FastAPI
from . import models
from .database import engine

# This line commands SQLAlchemy to create all tables from our models
models.Base.metadata.create_all(bind=engine)


# Create an instance of the FastAPI class with the updated name
app = FastAPI(
    title="BHV3 API",
    description="The central API for the BHV3 project.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    """
    This is the root endpoint of the API.
    It returns a welcome message.
    """
    # Updated welcome message to reflect the new project name
    return {"message": "Welcome to the BHV3 API"}