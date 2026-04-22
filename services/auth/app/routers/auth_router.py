from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db, UserModel
from app.infrastructure.security import SecurityProvider
from app.infrastructure.repositories import AuthRepository  
from app.application.auth_service import AuthService       
from .schemas import RegisterRequest
from app.infrastructure.email_provider import SMTPEmailProvider

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# --- Esquemas de Petición ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Inyección de Dependencias ---
def get_auth_service(db: Session = Depends(get_db)):
    repo = AuthRepository(db)
    email_provider = SMTPEmailProvider()
    return AuthService(repository=repo, email_provider=email_provider, security=SecurityProvider)

# --- Endpoints ---

@router.post("/register")
async def register(user: RegisterRequest, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    hashed_pass = SecurityProvider.hash_password(user.password)

    new_user = UserModel(
        email=user.email,
        password_hash=hashed_pass,
        role=user.role,
        is_verified=False 
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario registrado exitosamente. Por favor verifica tu correo."}

@router.post("/login-step-1")
async def login_1(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        # Esto generará el código, lo guardará en la DB y "enviará" el email
        return service.login_step_one(data.email, data.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/verify-2fa")
async def verify(email: EmailStr, code: str, service: AuthService = Depends(get_auth_service)):
    try:
        # Aquí validamos el código y generamos el JWT real
        return service.login_step_two(email, code)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    # Nivel 1: Público (Cualquiera entra)
@router.get("/test/public")
async def public_test():
    return {"message": "✅ Acceso Público: No necesitas token"}

# Nivel 2: Solo Logueados (Cualquier token válido entra)
@router.get("/test/private")
async def private_test(user: dict = Depends(SecurityProvider.get_current_user)):
    return {
        "message": "✅ Acceso Privado: Token válido detectado",
        "user_info": user
    }

# Nivel 3: Solo Admins (Token válido + Rol ADMIN)
@router.get("/test/admin")
async def admin_test(admin: dict = Depends(SecurityProvider.check_admin_role)):
    return {
        "message": "✅ Acceso Admin: Eres un administrador",
        "admin_email": admin.get("sub")
    }