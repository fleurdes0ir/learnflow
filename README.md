# LearnFlow

"GPS Jalur Karier" untuk mahasiswa IT — Graph Mapping + Gap Analysis berbasis mata kuliah kampus. **Bukan LMS.**

- Status: **W1 — fondasi backend** (FastAPI + PostgreSQL via Docker Compose).
- Konteks tim & AI agent: [`AGENTS.md`](AGENTS.md) · Arsitektur: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · Workflow tim: [`docs/TEAM_WORKFLOW.md`](docs/TEAM_WORKFLOW.md)

## Quickstart (localhost)
Prasyarat: Docker Engine + Docker Compose v2, Git.

```bash
cp .env.example .env          # lalu ganti POSTGRES_PASSWORD
docker compose up --build     # terminal 1
```
```bash
curl -s localhost:8000/healthz                # {"status":"ok",...}
curl -s localhost:8000/readyz                 # {"status":"ready","database":"up"}
curl -s localhost:8000/api/v1/meta/careers    # 3 role
```
Swagger (hanya `APP_ENV=development`): http://localhost:8000/docs

Stop: `Ctrl+C` lalu `docker compose down`. Hapus data DB: `docker compose down -v`.

## Tanpa Docker (backend saja)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check . && pytest
```

## Struktur
```
learnflow/
├── .github/            workflows (ci.yml aktif, cd.yml Phase 2) + PR template
├── backend/            FastAPI app, Dockerfile, tests
├── frontend/           React + Vite (Anggota 1, belum dibuat)
├── knowledge_base/     JSON statis (certifications.json, ...)
├── deploy/             Phase 2: Nginx + deploy.sh untuk GCP VM
├── docs/               ARCHITECTURE.md, TEAM_WORKFLOW.md
├── docker-compose.yml           postgres-db + backend-api
└── docker-compose.override.yml  DEV: hot-reload (otomatis dimuat)
```
