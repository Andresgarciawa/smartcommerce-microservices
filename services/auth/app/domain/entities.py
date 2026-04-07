# app/domain/entities.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

@dataclass
class User:
    id: int
    email: str
    password_hash: str
    role: UserRole
    is_active: bool = False  # Para el 2FA
    created_at: datetime = datetime.now()