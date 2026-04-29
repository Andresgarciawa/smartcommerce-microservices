FROM python:3.12-slim
WORKDIR /app

COPY services/catalog/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/catalog/ ./catalog_service/

EXPOSE 8001

CMD ["uvicorn", "catalog_service.app:app", "--host", "0.0.0.0", "--port", "8001"]