# api/main.py

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from . import crud, models, schemas, security
from .database import SessionLocal, engine

# --- DATABASE SCHEMA RESET ---
# This block forcefully drops and recreates all tables on every server start.
# This is ideal for development to ensure a clean slate.
print("--- RESETTING DATABASE: DROPPING ALL TABLES WITH CASCADE ---")
try:
    with engine.connect() as connection:
        with connection.begin():
            for tbl in reversed(models.Base.metadata.sorted_tables):
                # Using CASCADE to handle dependencies in PostgreSQL
                connection.execute(text(f'DROP TABLE IF EXISTS "{tbl.name}" CASCADE;'))
    print("--- DATABASE RESET COMPLETE ---")
except Exception as e:
    print(f"--- ERROR RESETTING DATABASE: {e} ---")
# -----------------------------

# This command creates the database tables with the correct, up-to-date schema
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BHV3 API",
    description="The central API for the BHV3 project, with a full hierarchical data model.",
    version="2.2.0"  # Version update for fix
)

# ==============================================================================
# Dependencies & Auth
# ==============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = security.verify_access_token(token, credentials_exception)
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def authenticate_user_login(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email)
    if not user or not security.verify_password(password, user.hashed_password):
        return None
    return user

# ==============================================================================
# API Routers
# ==============================================================================

router_auth = APIRouter(tags=["Authentication"])
router_users = APIRouter(tags=["Users"])
router_subjects = APIRouter(prefix="/subjects", tags=["Subjects"])
router_definitions = APIRouter(
    prefix="/subjects/{subject_id}/definitions", tags=["Behavior Definitions"]
)
router_scores = APIRouter(tags=["Scores"])


# ==============================================================================
# Endpoints
# ==============================================================================

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the BHV3 API"}


# --- Authentication ---
@router_auth.post("/token", summary="Login For Access Token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user_login(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password"
        )
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Users ---
@router_users.post("/users/", response_model=schemas.User, summary="Create New User")
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router_users.get(
    "/users/me", response_model=schemas.User, summary="Read Current User's Profile"
)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# --- Subjects ---
@router_subjects.post("/", response_model=schemas.Subject, summary="Create Subject")
def create_new_subject(
    subject: schemas.SubjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if crud.get_subject_by_name(db, name=subject.name, user_id=current_user.id):
        raise HTTPException(
            status_code=400, detail="A subject with this name already exists."
        )
    return crud.create_subject(db=db, subject=subject, user_id=current_user.id)


@router_subjects.get(
    "/", response_model=List[schemas.Subject], summary="List User's Subjects"
)
def list_user_subjects(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return crud.get_subjects_by_user(db=db, user_id=current_user.id)


# --- Behavior Definitions (Nested under Subjects) ---
@router_definitions.post(
    "/",
    response_model=schemas.BehaviorDefinition,
    summary="Create Definition for Subject",
)
def create_definition_for_subject(
    subject_id: int,
    definition: schemas.BehaviorDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.get_subject_and_verify_ownership(
        db=db, subject_id=subject_id, user_id=current_user.id
    )
    return crud.create_behavior_definition(
        db=db, definition=definition, subject_id=subject_id
    )


@router_definitions.get(
    "/",
    response_model=List[schemas.BehaviorDefinition],
    summary="List Definitions for Subject",
)
def list_definitions_for_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.get_subject_and_verify_ownership(
        db=db, subject_id=subject_id, user_id=current_user.id
    )
    return crud.get_definitions_by_subject(db=db, subject_id=subject_id)


# --- Scores (Independent but linked) ---
@router_scores.post("/scores/", response_model=schemas.Score, summary="Submit Score")
def submit_score(
    score: schemas.ScoreCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.get_subject_and_verify_ownership(
        db=db, subject_id=score.subject_id, user_id=current_user.id
    )
    return crud.create_behavior_score(db=db, score_data=score)


@router_subjects.get(
    "/{subject_id}/scores/averages/",
    response_model=List[schemas.BehaviorAverage],
    summary="Get Score Averages for Subject",
)
def get_score_averages_for_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    crud.get_subject_and_verify_ownership(
        db=db, subject_id=subject_id, user_id=current_user.id
    )
    return crud.get_score_averages_by_subject(db=db, subject_id=subject_id)


# --- Include Routers ---
app.include_router(router_auth)
app.include_router(router_users)
app.include_router(router_subjects)
app.include_router(router_definitions)
app.include_router(router_scores)
