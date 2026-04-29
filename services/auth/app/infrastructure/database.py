import os
import datetime
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, Boolean, create_engine, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.domain.entities import UserRole
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_verified = Column(Boolean, default=False)
    two_fa_code = Column(String, nullable=True)
    verification_codes = relationship("VerificationCode", back_populates="user")

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    code = Column(String(6), nullable=False) # El código de 6 dígitos
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    # Relación para acceder fácilmente al usuario
    user = relationship("UserModel", back_populates="verification_codes")