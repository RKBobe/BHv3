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

# ==============================================================================
# Reward System CRUD
# ==============================================================================

def create_reward_rule(db: Session, rule: schemas.RewardRuleCreate, subject_id: int):
    """Creates a new reward rule for a subject."""
    db_rule = models.RewardRule(**rule.model_dump(), subject_id=subject_id)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_reward_rules(db: Session, subject_id: int):
    """Retrieves all reward rules for a subject."""
    return db.query(models.RewardRule).filter(models.RewardRule.subject_id == subject_id).all()

def get_reward_account(db: Session, subject_id: int):
    """
    Retrieves the reward account for a subject.
    Creates one if it doesn't exist.
    """
    account = db.query(models.RewardAccount).filter(models.RewardAccount.subject_id == subject_id).first()
    if not account:
        account = models.RewardAccount(subject_id=subject_id, balance=0)
        db.add(account)
        db.commit()
        db.refresh(account)
    return account

def process_payout(db: Session, subject_id: int, amount: int, description: str):
    """
    Deducts an amount from the subject's reward account (payout).
    Creates a transaction record.
    """
    account = get_reward_account(db, subject_id)

    if account.balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds in reward account"
        )

    # Create Debit Transaction
    transaction = models.RewardTransaction(
        account_id=account.id,
        amount=-amount, # Negative for debit
        description=description
    )

    # Update Balance
    account.balance -= amount

    db.add(transaction)
    db.add(account) # Explicitly add account to session for update, though usually auto-tracked
    db.commit()
    db.refresh(account)
    return account

def evaluate_rewards(db: Session, subject_id: int):
    """
    Evaluates all reward rules for a subject against their current score averages.
    If a rule is met, creates a credit transaction.

    NOTE: In a real production system, we would need a way to prevent duplicate
    payouts for the same 'period' (e.g., store 'last_evaluated_at' or link
    transactions to specific time windows). For this MVP, it calculates based on
    all-time averages and pays out immediately if the threshold is met.
    Ideally, this should be triggered periodically and check 'since last check'.
    """
    rules = get_reward_rules(db, subject_id)
    if not rules:
        return {"message": "No rules defined for this subject."}

    account = get_reward_account(db, subject_id)

    # Get current averages
    # This returns a list of dicts: [{'definition': Obj, 'average_score': 85.5, ...}, ...]
    averages_data = get_score_averages_by_subject(db, subject_id)

    # Convert to a map for easy lookup by definition_id
    # Key: definition_id, Value: average_score
    avg_map = {
        item['definition'].id: item['average_score']
        for item in averages_data
        if item['average_score'] is not None
    }

    transactions_created = []

    for rule in rules:
        # 1. Determine the score to check
        score_to_check = None

        if rule.behavior_definition_id:
            # Specific behavior rule
            score_to_check = avg_map.get(rule.behavior_definition_id)
        else:
            # Global rule? (Average of averages? Or requires a global score concept?)
            # For MVP, let's skip global rules or implement simple avg of all scores
            pass

        if score_to_check is None:
            continue

        # 2. Check condition
        condition_met = False
        if rule.comparison_operator == "gt" and score_to_check > rule.threshold_value:
            condition_met = True
        elif rule.comparison_operator == "gte" and score_to_check >= rule.threshold_value:
            condition_met = True
        elif rule.comparison_operator == "lt" and score_to_check < rule.threshold_value:
            condition_met = True
        elif rule.comparison_operator == "lte" and score_to_check <= rule.threshold_value:
            condition_met = True
        elif rule.comparison_operator == "eq" and score_to_check == rule.threshold_value:
            condition_met = True

        # 3. Apply Reward (Blindly for MVP - see Note above)
        if condition_met:
            # Check if we should payout?
            # Real logic needed here: "Has this rule been triggered for this period?"
            # For MVP demo, we will just create the transaction.
            # USER WARNING: Clicking this multiple times will pay out multiple times.

            description = f"Reward earned: Rule {rule.id} met (Score {score_to_check} {rule.comparison_operator} {rule.threshold_value})"

            tx = models.RewardTransaction(
                account_id=account.id,
                amount=rule.reward_amount,
                description=description
            )
            account.balance += rule.reward_amount
            db.add(tx)
            transactions_created.append(description)

    if transactions_created:
        db.add(account)
        db.commit()
        db.refresh(account)
        return {
            "status": "Rewards applied",
            "new_balance": account.balance,
            "transactions": transactions_created
        }
    else:
        return {
            "status": "No new rewards earned",
            "current_balance": account.balance
        }
