import time
from fastapi import FastAPI
from app.infrastructure.database import Base, engine
from app.routers import auth_router

def create_tables():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            print("¡Tablas creadas con éxito!")
            break
        except Exception as e:
            print(f"Esperando a la base de datos... ({retries} reintentos restantes)")
            time.sleep(3)
            retries -= 1

create_tables()

app = FastAPI(title="Auth Service")

# Incluimos las rutas (Login, Registro, etc.)
app.include_router(auth_router.router)

@app.get("/")
def read_root():
    return {"message": "Servicio de Autenticación Activo"}