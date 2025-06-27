# api/models.py

from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, ForeignKey, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import the Base from database.py to be inherited by all models
from .database import Base

class User(Base):
    """Represents a user in the database. A User owns Subjects."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # A User has many Subjects. All other data is accessed through Subjects.
    subjects = relationship("Subject", back_populates="owner", cascade="all, delete-orphan")

class Subject(Base):
    """
    Represents a subject being scored (e.g., a person, a class).
    Owned by a User and contains BehaviorDefinitions and BehaviorScores.
    """
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="subjects")
    definitions = relationship("BehaviorDefinition", back_populates="subject", cascade="all, delete-orphan")
    scores = relationship("BehaviorScore", back_populates="subject", cascade="all, delete-orphan")

    # This ensures a user cannot have two subjects with the same name.
    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_id_subject_name_uc'),)

class BehaviorDefinition(Base):
    """
    Represents a defined behavior (e.g., "Completed Homework").
    Owned by a Subject.
    """
    __tablename__ = "behavior_definitions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    # Relationships
    subject = relationship("Subject", back_populates="definitions")
    scores = relationship("BehaviorScore", back_populates="definition", cascade="all, delete-orphan")

    # This ensures a behavior name is unique within its parent subject.
    __table_args__ = (UniqueConstraint('subject_id', 'name', name='_subject_id_bhv_name_uc'),)

class BehaviorScore(Base):
    """
    Represents a single score event. It links a Subject to a BehaviorDefinition
    on a specific date with a score value.
    """
    __tablename__ = "behavior_scores"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys to link the score event
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    behavior_definition_id = Column(Integer, ForeignKey("behavior_definitions.id"), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="scores")
    definition = relationship("BehaviorDefinition", back_populates="scores")
