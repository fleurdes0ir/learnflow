# LearnFlow — Technical Blueprint & System Architecture

**Versi:** 1.1 (UAS Cloud Computing — Local First & Cloud Ready)
Sumber: `learnfl0w.md` (Project LearnFlow). Ditambah catatan implementasi W1.

## 1. Overview
- **Tujuan:** penasihat karier dinamis ("GPS Jalur Karier") untuk mahasiswa IT berbasis Graph Mapping & Gap Analysis.
- **Batasan keras:** BUKAN LMS. Tidak ada materi, kuis, video. Murni visualisasi peta jalan, prasyarat, dan gap.
- **Pembeda:** mata kuliah riil kampus sebagai *anchor* kompetensi yang sudah dimiliki mahasiswa.

## 2. Tech stack
| Layer | Teknologi |
|---|---|
| Frontend | React (Vite) + Tailwind CSS + React Flow |
| Backend & AI | FastAPI async, satu service untuk REST + eksekusi AI |
| AI engine | LangGraph + LangChain (`StateGraph`, temperature 0.2) |
| DB | PostgreSQL (profil + roadmap JSONB) |
| Orkestrasi | Docker + Docker Compose |

**Phase 1 (utama):** semua jalan lokal via Docker Compose.
**Phase 2 (opsional):** GCP Compute Engine VM + Nginx reverse proxy, setelah free credit diklaim.

## 3. Alur LangGraph
1. **Node 0 — Input Sanitizer (level FastAPI):** `target_career` hanya dari enum `CareerTrack`. Mencegah halusinasi & prompt manipulation.
2. **Node 1 — Gap Analyzer:** bandingkan `completed_course_codes` dengan `industry_requirements` dari JSON statis di `knowledge_base/`.
3. **Node 2 — Roadmap Generator:** susun nodes & edges dari output Node 1.
4. **Node 3 — Validator (AI Guard):** cek prerequisite constraint. Lompatan logika → `loop_counter += 1` dan kembali ke Node 2. `loop_counter >= 3` → hentikan, kembalikan **Fallback Template**.

```
Request → [Node 0] → [Node 1] → [Node 2] → [Node 3] ──valid──▶ Result
                                    ▲          │
                                    └─invalid──┘ (loop_counter < 3)
                                               └─ loop_counter >= 3 ▶ Fallback Template
```

## 4. Global state
```python
class GraphState(TypedDict):
    student_profile: dict          # {"semester": int, "target_career": str, "completed_course_codes": list[str]}
    industry_requirements: list[str]
    generated_nodes: list[dict]
    generated_edges: list[dict]
    is_valid: bool
    validation_feedback: str
    loop_counter: int
```

## 5. Skema database
- **users:** `id` UUID PK · `name` str · `semester` int · `completed_courses` text[] (kode MK)
- **roadmaps:** `id` UUID PK · `user_id` UUID FK · `career_track` str · `graph_data` JSONB · `created_at` timestamptz
- **roadmap_tasks** *(usulan tambahan, lihat TEAM_WORKFLOW §5)*: `id` UUID PK (= `task_id`) · `status` · `result` JSONB · `error` · `created_at`

## 6. Mitigasi & protokol komunikasi
1. **Timeout:** endpoint generate memakai `task_id` + SSE (utama) / polling (fallback). Tidak ada request sinkron 15–30 dtk.
2. **Rate limit:** `slowapi`, 3 generate / IP / jam. Counter in-memory per proses → 1 worker di V1; Redis di V2.

## 7. Format output standar (React Flow)
```json
{
  "career_track": "Backend Developer",
  "roadmap_graph": {
    "nodes": [
      { "id": "n1", "label": "0072 - Algoritma", "source": "Kampus", "status": "DONE" },
      { "id": "n2", "label": "0001 - Basis Data", "source": "Kampus", "status": "DONE" },
      { "id": "n3", "label": "Docker Basics", "source": "Eksternal", "status": "RECOMMENDED_NOW" }
    ],
    "edges": [
      { "from": "n1", "to": "n3", "type": "prerequisite" },
      { "from": "n2", "to": "n3", "type": "prerequisite" }
    ]
  }
}
```
Ekstensi sertifikasi (node `Sertifikasi_Gratis` / `Sertifikasi_Berbayar` + `cert`): lihat `docs/TEAM_WORKFLOW.md` §1 dan §5.

## 8. Topologi infrastruktur
**Phase 1 (lokal):** `frontend-app` (Vite build → Nginx) · `backend-api` (FastAPI + Uvicorn + LangGraph) · `postgres-db` (volume persisten).
**Phase 2 (GCP):** Compute Engine VM menjalankan `docker-compose.yml`; Nginx host-level (80/443, SSL); firewall publik hanya 22/80/443.

## 9. Milestone
| # | Isi |
|---|---|
| M1 | Core engine & API lokal: FastAPI, skema PostgreSQL, alur LangGraph |
| M2 | Frontend React Flow + SSE/polling di localhost |
| M3 | Dockerfile tiap service + `docker compose up` penuh di lokal |
| M4 | Migrasi GCP (Phase 2): VM, clone repo, `.env` produksi, compose di cloud |

## 10. Status implementasi W1
- ✅ `postgres-db` + `backend-api` via Compose, `/healthz`, `/readyz`, `/api/v1/meta/careers`, CORS, slowapi terpasang.
- ✅ `knowledge_base/certifications.json` + test guard aturan (free first, tanpa harga, tanpa URL).
- ✅ CI (`.github/workflows/ci.yml`); CD ditulis tapi nonaktif (`GCP_ENABLED`).
- ⏳ `frontend-app` (M3), skema DB + migrasi, LangGraph (M1).
