from fastapi import FastAPI
from app.routers import enrichment_router
from app.infraestructure.database import engine, Base
from app.infraestructure import orm_models  # noqa: F401 - necesario para que SQLAlchemy registre los modelos

# Crea las tablas en la BD al iniciar (si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Enrichment Service",
    description="Enrichment Service para los libros",
    version="1.0.0"
)

app.include_router(enrichment_router.router)


@app.get("/health")
async def health():
    return {
        "service": "AI Enrichment Service",
        "status": "ok",
        "version": 1,
    }

@app.get("/")
async def root():
    return {
        "service": "AI Enrichment Service",
        "status": "online",
        "version": 1
    }

# Lógica para el Mock
@app.post("/enrichment/mock")
async def enrichment_mock(isbn: str):
    return {
        "isbn": isbn,
        "normalized_title": "Titulo Enriquecido (Mock)",
        "normalized_author": "Autor Estandarizado",
        "status": "success"
    }

