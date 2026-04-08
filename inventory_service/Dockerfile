FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY inventory_service ./inventory_service

EXPOSE 8000

CMD ["uvicorn", "inventory_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
