FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY royalens/royalens/ royalens/royalens/
COPY --from=frontend /app/frontend/dist frontend/dist

# MODEL_API_KEY se define en las variables de Coolify, nunca en la imagen.
# Monta un volumen en /data para conservar el historial entre despliegues.
ENV PYTHONPATH=/app/royalens ROYALENS_DATA=/data ROYALENS_MODE=real
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/estado', timeout=4)"
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
