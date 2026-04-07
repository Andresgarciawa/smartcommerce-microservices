import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SMTPEmailProvider:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")

    def send_verification_code(self, receiver_email: str, code: str):
        if not self.sender_email or not self.password:
            print("❌ Error: SMTP_USER o SMTP_PASSWORD no configurados en el .env")
            return
        
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = "Tu Código de Verificación - Biblioteca Online"

        body = f"""
        <html>
            <body>
                <h2>¡Hola!</h2>
                <p>Estás intentando acceder al Sistema de Biblioteca.</p>
                <p>Tu código de verificación de dos pasos es:</p>
                <h1 style="color: #4CAF50;">{code}</h1>
                <p>Este código expirará en unos minutos. Si no solicitaste esto, ignora este correo.</p>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        try:
            # Conexión segura con el servidor
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls() # Cifrado TLS
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, receiver_email, message.as_string())
            server.quit()
            print(f"✅ Correo enviado exitosamente a {receiver_email}")
        except Exception as e:
            print(f"❌ Error enviando correo: {e}")
            raise e