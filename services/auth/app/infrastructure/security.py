from fastapi import HTTPException, Security, Depends
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

class SecurityProvider:
    SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")
    ALGORITHM = "HS256"

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password, hashed_password) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_token(data: dict, expires_delta: timedelta):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SecurityProvider.SECRET_KEY, algorithm=SecurityProvider.ALGORITHM)
    
    @staticmethod
    def verify_jwt(auth: HTTPAuthorizationCredentials = Security(bearer_scheme)):
        
        try:
            token = auth.credentials
            payload = jwt.decode(token, SecurityProvider.SECRET_KEY, algorithms=[SecurityProvider.ALGORITHM])
            return payload  # Retorna los datos del usuario (email, role, etc.)
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    @staticmethod
    def get_current_user(auth: HTTPAuthorizationCredentials = Security(bearer_scheme)):
        """Valida que el token sea real y no haya expirado."""
        try:
            token = auth.credentials
            payload = jwt.decode(token, SecurityProvider.SECRET_KEY, algorithms=[SecurityProvider.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")

    @staticmethod
    def check_admin_role(current_user: dict = Depends(get_current_user)):
        """Valida específicamente si el usuario es ADMIN."""
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere ADMIN")
        return current_user