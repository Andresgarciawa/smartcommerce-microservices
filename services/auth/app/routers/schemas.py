from pydantic import BaseModel, EmailStr, Field
from app.domain.entities import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER

class Token(BaseModel):
    access_token: str
    token_type: str