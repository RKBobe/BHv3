# api/crud.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

# Import the models, schemas, and security utilities
from . import models, schemas, security

# --- User CRUD ---
def get_user_by_email(db: Session, email: str):
    """Retrieves a single user by their email address."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Creates a new user in the database with a hashed password."""
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Behavior Definition CRUD ---
def create_behavior_definition(db: Session, definition: schemas.BehaviorDefinitionCreate):
    """Creates a new behavior definition."""
    db_definition = models.BehaviorDefinition(**definition.model_dump())
    db.add(db_definition)
    db.commit()
    db.refresh(db_definition)
    return db_definition

def get_behavior_definitions(db: Session, skip: int = 0, limit: int = 100):
    """Retrieves a list of all behavior definitions."""
    return db.query(models.BehaviorDefinition).offset(skip).limit(limit).all()

# --- Score CRUD ---
def create_behavior_score(db: Session, user_id: int, score_data: schemas.ScoreCreate):
    """Creates a new behavior score for a specific user."""
    # This check ensures the referenced definition exists before creating a score.
    behavior_def = db.query(models.BehaviorDefinition).filter(models.BehaviorDefinition.id == score_data.behavior_definition_id).first()
    if not behavior_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Behavior definition with id {score_data.behavior_definition_id} not found"
        )

    db_score = models.BehaviorScore(**score_data.model_dump(), user_id=user_id)
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

def get_behavior_scores_by_user(db: Session, user_id: int):
    """Retrieves all scores recorded for a specific user."""
    return db.query(models.BehaviorScore).filter(models.BehaviorScore.user_id == user_id).all()
