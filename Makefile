.PHONY: setup backend backend-real frontend test build

setup:
	uv venv .venv --python 3.12
	uv pip install --python .venv/bin/python -r backend/requirements.txt pytest httpx
	cd frontend && npm install

# Modo demo: no usa la API ni gasta créditos. Corre cada uno en su terminal.
backend:
	ROYALENS_MODE=demo PYTHONPATH=royalens .venv/bin/uvicorn backend.main:app --reload --reload-dir backend --reload-dir royalens --port 8000

# API real: requiere MODEL_API_KEY en royalens/.env
backend-real:
	ROYALENS_MODE=real PYTHONPATH=royalens .venv/bin/uvicorn backend.main:app --reload --reload-dir backend --reload-dir royalens --port 8000

frontend:
	cd frontend && npm run dev

test:
	.venv/bin/python -m pytest -q

build:
	cd frontend && npm run build
