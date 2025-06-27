# api/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

# --- Subject Schemas ---
# The base schema for a Subject
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

# The schema used when creating a new Subject
class SubjectCreate(SubjectBase):
    pass

# The schema for returning a Subject, which includes its ID and nested definitions
class Subject(SubjectBase):
    id: int
    definitions: List['BehaviorDefinition'] = []

    class Config:
        from_attributes = True


# --- Behavior Definition Schemas ---
# Base schema for a Behavior Definition
class BehaviorDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None

# Schema for creating a new definition. The subject_id will be provided
# via the URL path, so it's not needed in the request body.
class BehaviorDefinitionCreate(BehaviorDefinitionBase):
    pass

# Schema for returning a definition, including its ID
class BehaviorDefinition(BehaviorDefinitionBase):
    id: int
    subject_id: int

    class Config:
        from_attributes = True

# We need to update the Subject schema now that BehaviorDefinition is fully defined
# to resolve the forward reference.
Subject.model_rebuild()


# --- Score Schemas ---
# The base for creating a score. It now requires a subject_id.
class ScoreBase(BaseModel):
    score: int
    date: date
    subject_id: int
    behavior_definition_id: int

class ScoreCreate(ScoreBase):
    pass

# The schema for returning a full score object
class Score(ScoreBase):
    id: int
    definition: BehaviorDefinition 

    class Config:
        from_attributes = True
        
# --- Score Average Schema ---
# This schema represents the calculated average for a single behavior
class BehaviorAverage(BaseModel):
    definition: BehaviorDefinition
    average_score: Optional[float] = None
    score_count: int

    class Config:
        from_attributes = True


# --- User Schemas ---
# The base schema for a User
class UserBase(BaseModel):
    email: EmailStr

# The schema for creating a new user
class UserCreate(UserBase):
    password: str

# The schema for returning a user profile. It now only contains
# a list of subjects, as all other data is accessed through them.
class User(UserBase):
    id: int
    is_active: bool
    subjects: List[Subject] = []

    class Config:
        from_attributes = True
        
# --- Token Schemas ---
class TokenData(BaseModel):
    email: Optional[str] = None
