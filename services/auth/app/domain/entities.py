from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# Aquí iría la lógica de "política mínima de credenciales"
def validate_password_strength(password: str) -> bool:
    return len(password) >= 8 and any(char.isdigit() for char in password)