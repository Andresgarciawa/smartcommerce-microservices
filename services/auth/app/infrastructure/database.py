from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from app.domain.entities import UserRole

Base = declarative_base()

class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_verified = Column(Boolean, default=False)