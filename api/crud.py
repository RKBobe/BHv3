# api/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from . import models, schemas, security

# ==============================================================================
# Security & Helper Functions
# ==============================================================================

def get_subject_and_verify_ownership(db: Session, subject_id: int, user_id: int):
    """
    A crucial security function. Fetches a subject by its ID and verifies
    that it is owned by the currently authenticated user.
    Raises an HTTPException if not found or if ownership check fails.
    """
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this subject")
    return subject

# ==============================================================================
# User CRUD
# ==============================================================================

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ==============================================================================
# Subject CRUD
# ==============================================================================

def get_subject_by_name(db: Session, name: str, user_id: int):
    return db.query(models.Subject).filter(
        models.Subject.name == name,
        models.Subject.user_id == user_id
    ).first()

def create_subject(db: Session, subject: schemas.SubjectCreate, user_id: int):
    db_subject = models.Subject(**subject.model_dump(), user_id=user_id)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subjects_by_user(db: Session, user_id: int):
    return db.query(models.Subject).filter(models.Subject.user_id == user_id).all()

# ==============================================================================
# Behavior Definition CRUD
# ==============================================================================

def create_behavior_definition(db: Session, definition: schemas.BehaviorDefinitionCreate, subject_id: int):
    """Creates a new definition and links it to a subject."""
    db_definition = models.BehaviorDefinition(**definition.model_dump(), subject_id=subject_id)
    db.add(db_definition)
    db.commit()
    db.refresh(db_definition)
    return db_definition

def get_definitions_by_subject(db: Session, subject_id: int):
    """Retrieves all behavior definitions for a single subject."""
    return db.query(models.BehaviorDefinition).filter(models.BehaviorDefinition.subject_id == subject_id).all()

# ==============================================================================
# Behavior Score CRUD
# ==============================================================================

def create_behavior_score(db: Session, score_data: schemas.ScoreCreate):
    """
    Creates a new score. Note: Ownership is validated in the main API endpoint
    before this function is ever called.
    """
    # A final check to ensure the definition belongs to the subject being scored.
    definition = db.query(models.BehaviorDefinition).filter(
        models.BehaviorDefinition.id == score_data.behavior_definition_id,
        models.BehaviorDefinition.subject_id == score_data.subject_id
    ).first()
    if not definition:
        raise HTTPException(
            status_code=400,
            detail="Behavior definition does not belong to the specified subject."
        )

    db_score = models.BehaviorScore(**score_data.model_dump())
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

def get_score_averages_by_subject(db: Session, subject_id: int):
    """
    Calculates the average score for each behavior definition
    associated with a single subject.
    """
    definitions = get_definitions_by_subject(db=db, subject_id=subject_id)
    
    results = (
        db.query(
            models.BehaviorScore.behavior_definition_id,
            func.avg(models.BehaviorScore.score).label("average_score"),
            func.count(models.BehaviorScore.id).label("score_count"),
        )
        .filter(models.BehaviorScore.subject_id == subject_id)
        .group_by(models.BehaviorScore.behavior_definition_id)
        .all()
    )
    
    averages_map = {
        result.behavior_definition_id: {
            "average_score": float(result.average_score) if result.average_score else None,
            "score_count": result.score_count,
        }
        for result in results
    }

    response_data = []
    for definition in definitions:
        avg_data = averages_map.get(definition.id, {"average_score": None, "score_count": 0})
        response_data.append({
            "definition": definition,
            "average_score": avg_data["average_score"],
            "score_count": avg_data["score_count"]
        })
    return response_data
