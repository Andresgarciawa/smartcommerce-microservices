FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el contenido de la carpeta actual al WORKDIR (/app)
COPY . .

# Comando para ejecutar uvicorn
# Importante: "app.main:app" significa: busca el archivo main.py dentro de la carpeta app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]