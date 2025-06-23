# api/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Schema for the data inside the JWT
class TokenData(BaseModel):
    email: Optional[str] = None

# Schemas for User data handling
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True