# AGENTS.md — konteks untuk OpenCode / AI coding agent

Baca file ini penuh sebelum menulis kode. Detail lanjut: `docs/ARCHITECTURE.md`, `docs/TEAM_WORKFLOW.md`.

## Apa ini
**LearnFlow** = "GPS Jalur Karier" untuk mahasiswa IT (Graph Mapping + Gap Analysis).
Memakai kode mata kuliah kampus riil (mis. `0072 Algoritma`, `0001 Basis Data`) sebagai anchor kompetensi.

## ATURAN KERAS (jangan dilanggar)
1. **BUKAN LMS.** Jangan buat fitur materi, video, kuis, tugas, progress belajar, atau penilaian.
2. **Local-First.** Semua harus jalan via `docker compose up --build` di localhost. Jangan mengasumsikan GCP/cloud credit. Jangan menambah dependency ke layanan cloud berbayar.
3. **Sertifikasi:** `free_options` selalu sebelum `paid_options`. Dilarang menulis harga/nominal dan URL mentah — hanya `search_query`.
4. **Node 0:** `target_career` hanya boleh nilai enum `CareerTrack` (`backend/app/schemas/enums.py`). Validasi di layer FastAPI SEBELUM LLM dipanggil.
5. **Node 3 gagal ≥ 3 kali (`loop_counter >= 3`)** → hentikan graph, kembalikan Fallback Template JSON. Tidak boleh ada loop tak terbatas.
6. **Secret** hanya lewat environment. Jangan commit `.env`. Jangan hardcode API key. Jangan log secret.
7. **Test tidak boleh memanggil LLM asli.** Mock provider.
8. Generate roadmap lambat (15–30 dtk) → pakai SSE/polling dengan `task_id`, bukan request sinkron. Rate limit `slowapi` (3/jam/IP) pada endpoint generate.

## Stack
FastAPI (async) · SQLAlchemy 2 async + asyncpg · PostgreSQL 16 · LangGraph/LangChain (temperature 0.2) ·
React + Vite + Tailwind + React Flow (folder `frontend/`, belum dibuat) · Docker Compose.

## Peta repo
```
backend/app/main.py            entrypoint, CORS, /healthz, /readyz, /api/v1/meta/careers
backend/app/core/config.py     SATU-SATUNYA tempat baca env (pydantic-settings)
backend/app/core/rate_limit.py slowapi limiter
backend/app/db/session.py      async engine (lazy)
backend/app/schemas/           Pydantic + enum domain
backend/app/agents/            LangGraph nodes (Milestone 1) — node_0..node_3, state.py, graph.py
backend/tests/                 pytest (TestClient, tanpa DB/LLM asli)
knowledge_base/                JSON statis (certifications, requirements, fallback)
deploy/                        Phase 2 (GCP) — jangan disentuh sebelum diminta
```

## Perintah
```bash
cp .env.example .env                              # sekali
docker compose up --build                         # jalankan (hot-reload via override)
curl -s localhost:8000/healthz
cd backend && pip install -r requirements-dev.txt
cd backend && ruff check . && ruff format --check . && pytest
```

## Konvensi kode
- Python 3.12, **fully typed**, Pydantic v2, `async def` untuk I/O. Format & lint: `ruff` (line 100).
- Satu tanggung jawab per modul. Logika bisnis di `app/services/` & `app/agents/`, bukan di route.
- Route baru → router di `app/api/` lalu `include_router` di `main.py` dengan prefix `/api/v1`.
- Validator Node 3 harus **deterministik dulu** (cek siklus/topological order, prasyarat, rule sertifikasi); LLM hanya untuk pengecekan semantik tambahan.
- Commit: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`). Branch dari `dev`: `feat/*`, `fix/*`, `chore/*`. Jangan commit ke `main`.
- Frontend: komponen fungsional + hooks, Tailwind, React Flow custom node. Backend base URL dari `VITE_API_BASE_URL`.

## Kontrak data (ringkas) — format node React Flow
`source` ∈ `Kampus | Eksternal | Sertifikasi_Gratis | Sertifikasi_Berbayar`;
`status` ∈ `DONE | RECOMMENDED_NOW | UPCOMING`. Node sertifikasi membawa `cert: {provider, search_query}`.
Selengkapnya: `docs/TEAM_WORKFLOW.md` §5.
