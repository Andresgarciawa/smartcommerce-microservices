FROM python:3.12-slim
WORKDIR /app
COPY app /app
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx pydantic python-dotenv python-multipart
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
