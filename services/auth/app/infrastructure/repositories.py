import secrets
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.infrastructure.database import VerificationCode, UserModel
class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def save_2fa_code(self, user_id: int, code: str):
        """
        Guarda el código de 6 dígitos en la tabla de verificación.
        """
        # Definimos que el código expira en 10 minutos
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        new_verification = VerificationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            is_used=False
        )
        
        try:
            self.db.add(new_verification)
            self.db.commit()
            self.db.refresh(new_verification)
            return new_verification
        except Exception as e:
            self.db.rollback()
            print(f"Error al guardar el código 2FA: {e}")
            raise e
        
    def verify_2fa(self, email: str, code: str) -> bool:
        # Buscamos al usuario por email para obtener su ID
        user = self.get_by_email(email)
        if not user:
            return False

        verification = self.db.query(VerificationCode).filter(
            VerificationCode.user_id == user.id,
            VerificationCode.code == code,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.now(timezone.utc)
        ).order_by(VerificationCode.created_at.desc()).first()

        if verification:
            verification.is_used = True
            try:
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Error al marcar código como usado: {e}")
                return False
        
        return False