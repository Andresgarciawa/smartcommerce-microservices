import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de la base de datos leída desde variable de entorno (configurada en Docker Compose)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@db:5432/enrichment_db")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Función para obtener una sesión de base de datos (usar como dependencia en FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()