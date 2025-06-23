# api/crud.py

from sqlalchemy.orm import Session

# --- MODIFIED IMPORTS ---
from . import models
from .schemas import UserCreate
from .security import get_password_hash

# Note: get_user_by_email function remains the same.
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# This function now calls the imported hashing function directly.
def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Add this function to the end of api/crud.py

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticates a user. Returns the user object if successful, otherwise None.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user