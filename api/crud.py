# api/crud.py

from sqlalchemy.orm import Session
from api.models import User
from api.schemas import UserCreate
# --- MODIFIED IMPORT ---
# We now import BOTH functions we need from the security module.
from api.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- NEW FUNCTION, NOW CORRECTED ---
def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticates a user. Returns the user object if successful, otherwise None.
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    # We now call the imported 'verify_password' function directly.
    if not verify_password(password, user.hashed_password):
        return None
    return user