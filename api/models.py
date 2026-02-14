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
    reward_account = relationship("RewardAccount", uselist=False, back_populates="subject", cascade="all, delete-orphan")
    reward_rules = relationship("RewardRule", back_populates="subject", cascade="all, delete-orphan")

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


class RewardAccount(Base):
    """
    Tracks the accumulated 'balance' for a Subject.
    """
    __tablename__ = "reward_accounts"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)  # Stored in smallest currency unit (e.g., cents) or points

    # Relationships
    subject = relationship("Subject", back_populates="reward_account")
    transactions = relationship("RewardTransaction", back_populates="account", cascade="all, delete-orphan")


class RewardRule(Base):
    """
    Defines a rule for earning rewards.
    Example: "If avg score of Definition X > 80, earn 100 points".
    """
    __tablename__ = "reward_rules"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    behavior_definition_id = Column(Integer, ForeignKey("behavior_definitions.id"), nullable=True) # Optional: global rule vs specific behavior

    threshold_value = Column(Integer, nullable=False) # e.g., 80
    reward_amount = Column(Integer, nullable=False)   # e.g., 100 (cents/points)
    comparison_operator = Column(String, default="gt") # gt, lt, eq, gte, lte

    # Relationships
    subject = relationship("Subject", back_populates="reward_rules")
    behavior_definition = relationship("BehaviorDefinition")


class RewardTransaction(Base):
    """
    Records a credit (earning) or debit (payout).
    """
    __tablename__ = "reward_transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("reward_accounts.id"), nullable=False)
    amount = Column(Integer, nullable=False) # Positive for credit, Negative for debit
    description = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    account = relationship("RewardAccount", back_populates="transactions")
