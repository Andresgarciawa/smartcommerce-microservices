import secrets
from datetime import timedelta

class AuthService:
    def __init__(self, repository, email_provider, security):
        self.repo = repository
        self.email = email_provider
        self.security = security

    def login_step_one(self, email, password):
        # 1. Buscar al usuario
        user = self.repo.get_by_email(email)
        
        # 2. Validar credenciales
        if user and self.security.verify_password(password, user.password_hash):
            # 3. Generar código aleatorio de 6 dígitos SEGURO
            code = self.generate_random_code()
            
            self.email.send_verification_code(email, code)
            
            # 4. Persistencia: Guardar el código en la tabla (VerificationCode)
            self.repo.save_2fa_code(user.id, code)
            
            return {"message": "Código enviado al correo"}
        
        raise Exception("Credenciales inválidas")
    
    def generate_random_code(self):

        return "".join(secrets.choice("0123456789") for _ in range(6))

    def login_step_two(self, email, code):
        if self.repo.verify_2fa(email, code):
            user = self.repo.get_by_email(email)
            token = self.security.create_token(
                {"sub": user.email, "role": user.role}, 
                expires_delta=timedelta(hours=2)
            )
            return {"access_token": token, "token_type": "bearer"}
        raise Exception("Código incorrecto o expirado")