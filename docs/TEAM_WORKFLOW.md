# TEAM_WORKFLOW — LearnFlow

**Tim:** 2 orang · **Mata kuliah:** UAS Cloud Computing · **Versi dokumen:** 1.0 (2026-10-21)
**Dokumen pasangan:** `learnfl0w.md` / `docs/ARCHITECTURE.md` (blueprint teknis) · `AGENTS.md` (konteks AI agent)
**Target V1.0:** akhir November 2026 · **Prinsip:** Local-First — semuanya harus jalan di `docker compose up` di laptop sebelum GCP disentuh.

---

## 0. Aturan Emas

1. **BUKAN LMS.** Tidak ada materi, video, kuis, tugas, atau skor belajar. Fitur yang menyerupai itu ditolak di review.
2. **Local-First.** Phase 1 selesai (compose lokal hijau) → baru Phase 2 (GCP). Tidak ada kode yang hanya bisa jalan di cloud.
3. **Kontrak dulu, kode kemudian.** Frontend dan backend bergantung pada kontrak di §5. Ubah kontrak = PR sendiri yang di-approve dua orang.
4. **Tidak ada commit langsung ke `main` atau `dev`.** Semua lewat PR + CI hijau + 1 approval.
5. **Push = checkpoint.** Commit kecil dan sering, push minimal di akhir setiap sesi kerja. Sesi AI bisa putus, limit bisa habis, laptop bisa mati; yang belum di-push dianggap tidak ada.

---

## 1. Modul Rekomendasi Sertifikasi (Free First, Paid Later)

### 1.1 Posisi modul (dalam batas Non-LMS)
Sertifikasi hanyalah **node rekomendasi eksternal** di graph. LearnFlow tidak menampung, menyajikan, atau menilai materi sertifikasi apa pun. Output modul ini = penunjuk ("cari ini di mana pun kamu belajar"), bukan konten.

### 1.2 Struktur `knowledge_base/certifications.json`

```
{
  "schema_version": "1.0",
  "last_reviewed": "YYYY-MM-DD",
  "policy": { ... },                    // metadata aturan, dibaca manusia
  "roles": {
    "Backend Developer" | "Data Scientist" | "DevOps Engineer": {
      "free_options": [ <Option>, ... ],   // WAJIB key pertama, tidak boleh kosong
      "paid_options": [ <Option>, ... ]    // WAJIB key kedua
    }
  }
}
```

| Field `<Option>` | Tipe | Aturan |
|---|---|---|
| `id` | string slug | Unik di seluruh file. Dipakai sebagai whitelist ID oleh Node 2. |
| `provider` | enum | Free: `FreeCodeCamp`, `Kaggle`, `Cisco Networking Academy`, `Google Cloud Skills Boost`, `Microsoft Applied Skills`. Paid: `AWS`, `Oracle`, `CNCF / Linux Foundation` (CKA), `CompTIA`. |
| `title` | string | Nama program, deskriptif. Tanpa harga. |
| `level` | enum | `beginner` · `intermediate` · `advanced` |
| `skills` | string[] | Tag skill yang dicakup. Harus cocok dengan tag di `*_req.json` (Node 1). |
| `prerequisite_skills` | string[] | Skill yang sebaiknya dikuasai dulu. Dipakai untuk membuat edge. |
| `search_query` | string | **Satu-satunya** penunjuk sumber. Bukan URL. |

Contoh (potongan; file lengkap sudah ada di repo):

```json
"Backend Developer": {
  "free_options": [
    {
      "id": "fcc-relational-database",
      "provider": "FreeCodeCamp",
      "title": "Relational Database Certification",
      "level": "beginner",
      "skills": ["sql", "postgresql", "git", "linux-cli"],
      "prerequisite_skills": [],
      "search_query": "freeCodeCamp Relational Database certification"
    }
  ],
  "paid_options": [
    {
      "id": "aws-developer-associate",
      "provider": "AWS",
      "title": "AWS Certified Developer - Associate",
      "level": "intermediate",
      "skills": ["cloud-fundamentals", "ci-cd", "rest-api"],
      "prerequisite_skills": ["rest-api", "cloud-fundamentals"],
      "search_query": "AWS Certified Developer Associate exam guide"
    }
  ]
}
```

Cakupan awal: Backend 5 free + 3 paid · Data Scientist 6 free + 3 paid · DevOps 4 free + 4 paid.

### 1.3 Logika pemilihan (deterministik — dijalankan KODE, bukan LLM)

1. Ambil `gap_skills` dari Node 1 (skill target yang belum tercakup mata kuliah kampus siswa).
2. **Kandidat** = opsi role terpilih yang `skills ∩ gap_skills ≠ ∅`.
3. **Free dulu:** urutkan `free_options` kandidat berdasar `level` (beginner → advanced), lalu urutan di file. Ambil maksimal 4. Status node: `RECOMMENDED_NOW` bila semua `prerequisite_skills`-nya sudah terpenuhi, selain itu `UPCOMING`.
4. **Paid belakangan:** `paid_options` kandidat hanya dimunculkan **setelah** blok free, maksimal 2, status selalu `UPCOMING`, dengan edge `prerequisite` dari node free yang skill-nya tumpang tindih.
5. **LLM hanya boleh memilih/mengurutkan `id` dari whitelist kandidat.** Teks `title`, `provider`, dan `search_query` selalu diambil dari JSON oleh kode. LLM tidak pernah menulis teks sertifikasi. Ini mekanisme paling kuat melawan halusinasi harga dan link.

### 1.4 Aturan keras dan penegakannya

| Aturan | Lapis 1 — CI (sudah ada) | Lapis 2 — Desain | Lapis 3 — Runtime (Node 3) |
|---|---|---|---|
| `free_options` di atas `paid_options` | `test_free_options_come_first` | Kode menyusun urutan | Validator menolak graph yang node berbayarnya muncul sebelum node gratis |
| Tidak ada nominal harga | `test_no_price_and_no_raw_url` | LLM tidak menulis teks sertifikasi (whitelist ID) | Regex scrub pada semua `label`/teks hasil LLM; ada match → invalid |
| Tidak ada link mentah | idem | Hanya `search_query` | Regex `https?://\|www\.` pada output → invalid |
| Hanya role di enum | `test_roles_match_career_enum` | Node 0 | — |

### 1.5 Tampilan (tanggung jawab Anggota 1)
Frontend membangun tautan pencarian dari `search_query` (`encodeURIComponent`, `target="_blank"`, `rel="noopener noreferrer"`) dan memberi label tombol "Cari program ini". Backend dan LLM tidak pernah mengirim URL. Tambahkan disclaimer permanen di UI: *"Ketersediaan, status gratis, dan biaya program dapat berubah. Cek langsung di penyedia."*

---

## 2. Pembagian Tugas (2 Orang) & Checklist

### 2.1 Kepemilikan

| | Anggota 1 — Frontend & Integration Lead | Anggota 2 — Backend, AI & Infrastructure Lead |
|---|---|---|
| Folder | `frontend/` | `backend/`, `knowledge_base/`, `deploy/`, `docker-compose*.yml`, `.github/` |
| Bersama | `docs/`, kontrak API (§5), demo, laporan UAS | |

Reviewer silang: setiap PR satu orang di-review orang lainnya.

### 2.2 Checklist Anggota 1 — Frontend & Integration Lead

**W1 (19–25 Okt) — Persiapan**
- [ ] Clone repo, baca `AGENTS.md` + §5 dokumen ini
- [ ] Jalankan `docker compose up --build`, buka `/docs`, tes `/api/v1/meta/careers` dari browser (cek CORS dari `localhost:5173`)
- [ ] Review PR fondasi backend Anggota 2 (minimal 1 komentar substantif)

**W2 (26 Okt–1 Nov) — UI shell & form asesmen**
- [ ] `npm create vite@latest frontend -- --template react`, pasang Tailwind CSS
- [ ] ESLint + Prettier, `VITE_API_BASE_URL` di `.env.example` frontend
- [ ] Layout, routing, design token (warna, tipografi, status node)
- [ ] Form Asesmen: semester, dropdown target karier (dari `GET /meta/careers`, bukan hardcode), multi-select kode MK dengan pencarian (dari `GET /meta/courses`)
- [ ] Validasi form di sisi klien (semester 1–14, minimal 1 MK, role wajib)
- [ ] Mock API (MSW) sesuai kontrak §5 supaya tidak menunggu backend

**W3 (2–8 Nov) — Visualisasi React Flow**
- [ ] Custom node: `Kampus`, `Eksternal`, `Sertifikasi_Gratis`, `Sertifikasi_Berbayar` (visual berbeda + badge status `DONE`/`RECOMMENDED_NOW`/`UPCOMING`)
- [ ] Auto-layout graph (dagre atau elkjs), zoom/pan, minimap, legenda
- [ ] Render dari fixture JSON lokal (termasuk kasus `is_fallback: true`)
- [ ] Panel detail node: tampilkan `label`, sumber, dan untuk sertifikasi: provider + tombol "Cari program ini" (§1.5)

**W4 (9–15 Nov) — Integrasi asinkron**
- [ ] Hook `useRoadmapStream`: `POST /roadmaps` → `EventSource` ke `/stream`; fallback otomatis ke polling `GET /roadmaps/{task_id}` bila SSE putus
- [ ] UI progres per node (Node 0 → 3, tampilkan `loop_counter` bila > 0)
- [ ] State error: 422 (input), 429 (rate limit, tampilkan sisa waktu tunggu), `failed`, banner "Roadmap standar ditampilkan" saat `is_fallback`
- [ ] **Hari integrasi Jumat 13 Nov** dengan backend asli

**W5 (16–22 Nov) — Polishing & containerization**
- [ ] Panel Rekomendasi Sertifikasi: blok Gratis di atas, blok Berbayar di bawah, disclaimer §1.5
- [ ] Responsif (laptop + HP), empty/loading state, aksesibilitas dasar (kontras, fokus keyboard)
- [ ] `frontend/Dockerfile` multi-stage (node build → nginx) + `frontend/nginx.conf` (SPA fallback)
- [ ] Tambah service `frontend-app` ke `docker-compose.yml` (koordinasi dengan Anggota 2; port `127.0.0.1:8080`)

**W6 (23–30 Nov) — Freeze & laporan**
- [ ] Bugfix saja, tanpa fitur baru
- [ ] Skrip demo + screenshot untuk laporan UAS
- [ ] Bagian laporan: UI/UX, alur pengguna, kontrak API

### 2.3 Checklist Anggota 2 — Backend, AI & Infrastructure Lead

**W1 (19–25 Okt) — Fondasi** *(paket repo ini)*
- [x] Struktur repo, `.gitignore`, `.env.example`
- [x] FastAPI async: `/healthz`, `/readyz`, `/api/v1/meta/careers`, CORS, slowapi terpasang
- [x] Dockerfile multi-stage non-root, `docker-compose.yml` (backend-api + postgres-db) + override hot-reload
- [x] `knowledge_base/certifications.json` + test guard
- [x] `ci.yml` aktif, `cd.yml` ditulis (nonaktif)
- [ ] Jalankan `docker compose up --build` + 4 perintah verifikasi di laptop sendiri (hasil belum diuji di sesi pembuatan)
- [ ] `git init`, push ke GitHub, buat `dev`, aktifkan branch protection (§4.2)

**W2 (26 Okt–1 Nov) — Data & Node 0**
- [ ] **Bekukan kontrak API §5 (target Senin 26 Okt)** dan kirim ke Anggota 1
- [ ] SQLAlchemy models + Alembic migration: `users`, `roadmaps`, `roadmap_tasks`
- [ ] `GET /api/v1/meta/courses` (sumber: `knowledge_base/courses.json` dari kurikulum kampus)
- [ ] `knowledge_base/{backend,data_scientist,devops}_req.json` — kode MK riil → skill tag
- [ ] Node 0: schema request Pydantic (enum `CareerTrack`, pola kode MK, batas panjang list), `GraphState`

**W3 (2–8 Nov) — Node 1 & provider LLM**
- [ ] Node 1 Gap Analyzer: murni Python (tanpa LLM), unit test
- [ ] Abstraksi provider LLM (`LLMProvider` protocol): Gemini / Claude / GPT / DeepSeek via config; timeout + retry terbatas
- [ ] `FakeLLMProvider` untuk test (deterministik) — CI tidak boleh memanggil LLM asli
- [ ] Pemilih sertifikasi §1.3 (kode murni) + test

**W4 (9–15 Nov) — Node 2, Node 3, endpoint**
- [ ] Node 2 Roadmap Generator: structured output (Pydantic), temperature 0.2, LLM hanya memilih ID whitelist untuk sertifikasi
- [ ] Node 3 Validator: **cek deterministik dulu** (graph acyclic via topological sort, tidak ada node yatim, prasyarat terpenuhi, aturan §1.4 lapis 3); LLM opsional untuk semantik
- [ ] Loop `loop_counter`, `>= 3` → `fallback_template.json` (`is_fallback: true`)
- [ ] Endpoint §5: `POST /roadmaps` (slowapi `3/hour`), `GET /roadmaps/{id}`, `GET /roadmaps/{id}/stream` (SSE)
- [ ] Simpan hasil ke `roadmaps.graph_data` (JSONB)
- [ ] **Hari integrasi Jumat 13 Nov**

**W5 (16–22 Nov) — Orkestrasi & Phase 2 prep**
- [ ] Review `knowledge_base/*` terakhir; semua test hijau
- [ ] Compose penuh 3 service; satu perintah dari clone bersih sampai demo jalan
- [ ] Siapkan `deploy/` (sudah ada draf): `deploy.sh`, `nginx/learnflow.conf`, runbook VM
- [ ] **Gate GCP (Senin 16 Nov):** credit sudah diklaim? Jika belum → aktifkan Plan B (§3)
- [ ] PR `dev` → `main`, tag `v1.0.0-rc1`

**W6 (23–30 Nov) — Cloud & penutupan**
- [ ] Bootstrap VM + deploy pertama manual (ikuti `deploy/README.md`)
- [ ] Isi GitHub Secrets/Variables, set `GCP_ENABLED=true`, uji CD dengan `workflow_dispatch`
- [ ] Smoke test dari luar VM (`curl` ke IP publik), cek firewall hanya 22/80/443
- [ ] Tag `v1.0.0`; bagian laporan: arsitektur, Docker, CI/CD, deployment

### 2.4 Checklist bersama
- [ ] Review silang semua PR (maks. 24 jam)
- [ ] Demo kering (dry run) 2× sebelum hari presentasi, termasuk skenario LLM gagal → fallback
- [ ] Laporan UAS: tiap anggota menulis bagiannya, digabung di `docs/`

---

## 3. Timeline Staging Version

### 3.1 Kalender V1.0

| Minggu | Tanggal | Fokus | Gerbang keluar |
|---|---|---|---|
| W1 | 19–25 Okt | Fondasi repo + backend | `docker compose up` hijau, CI hijau di GitHub |
| W2 | 26 Okt–1 Nov | Skema DB, Node 0, form + UI shell | Kontrak API beku; form jalan dengan MSW |
| W3 | 2–8 Nov | Node 1, provider LLM, React Flow | Gap analysis teruji; graph render dari fixture |
| W4 | 9–15 Nov | Node 2/3, SSE, integrasi | **Alur end-to-end jalan lokal (13 Nov)** |
| W5 | 16–22 Nov | Sertifikasi di UI, compose penuh | **Feature freeze Minggu 22 Nov**; `v1.0.0-rc1` |
| W6 | 23–30 Nov | GCP deploy, bugfix, laporan | `v1.0.0` ≤ 29 Nov; submit 30 Nov |

> Konfirmasi tanggal pengumpulan pasti ke dosen. "Akhir November" tidak cukup untuk perencanaan.

### 3.2 Staging V1.0 — Target UAS Cloud Computing (deadline akhir Nov 2026)
**Scope:** MVP penuh Local-First via Docker Compose + GCP VM Deployment Ready (Phase 2).
**Rantai milestone:** Form Asesmen → LangGraph (Node 0–3) → React Flow dengan status node & rekomendasi sertifikasi → Docker Compose lokal → migrasi ke GCP VM *(bila kredit aktif)*.

**Definition of Done V1.0**
- [ ] Clone bersih → `cp .env.example .env` → `docker compose up --build` → aplikasi bisa dipakai tanpa langkah manual lain
- [ ] Alur lengkap: form → progres SSE → graph dengan node Kampus/Eksternal/Sertifikasi (gratis di atas berbayar)
- [ ] Node 3 gagal 3× → fallback tampil, aplikasi tidak crash
- [ ] Rate limit 429 tertangani di UI
- [ ] CI hijau di `main`; test tidak memanggil LLM asli
- [ ] Tidak ada secret di riwayat Git; tidak ada harga/URL di output sertifikasi
- [ ] Phase 2: VM menjalankan compose yang sama, Nginx di port 80, CD via GitHub Actions **atau** runbook manual terdokumentasi

**Gate GCP (16 Nov) dan Plan B:** bila free credit belum aktif, V1.0 diserahkan sebagai Local-First lengkap + artefak deploy (`deploy/`, `cd.yml`, runbook) yang sudah ditinjau. Jangan menunda keputusan ini; diskusikan dengan dosen apakah deploy lokal dengan bukti artefak diterima.

### 3.3 Staging V2.0 — Post-UAS / Refinement
**Scope:** optimasi performa dan efisiensi biaya API.
- [ ] Redis: cache respons AI (kunci = hash dari `{career, sorted(course_codes)}`), rate limit storage multi-worker
- [ ] PWA (manifest + service worker; cache aset statis, bukan respons personal)
- [ ] Dynamic Knowledge Base Update: JSON di `knowledge_base/` bisa diperbarui tanpa rebuild image (volume + endpoint admin/skrip reload), versi skema, `last_reviewed` diaudit
- [ ] Metrik biaya: token per generate, cache hit ratio

### 3.4 Staging V3.0 — Journal & Research
**Scope:** pengujian akademis dan publikasi.
- [ ] Load testing infrastruktur cloud (k6 atau Locust): latensi p50/p95, throughput, titik jenuh, biaya per 1.000 roadmap
- [ ] System Usability Scale (SUS) pada sampel mahasiswa: rancang protokol, izin responden, minimal ~20–30 peserta agar skor bermakna
- [ ] Evaluasi kualitas roadmap (mis. kesepakatan dengan penilaian dosen/praktisi atas sampel)
- [ ] Draf naskah jurnal: pendahuluan, metode, hasil, diskusi

---

## 4. Strategi GitHub Production & CI/CD

### 4.1 Branching

```
main  ●───────────────────────●───────────────●   stabil, deploy GCP, tag vX.Y.Z
       \                     / (PR, merge commit)
dev     ●──●──────●──●──────●──────●──────────     integrasi, diuji lokal
         \/ \    / \/      \    /
feat/*   ●   ●──●   ●       ●──●                   feat/*  fix/*  chore/*  (dari dev)
```

| Branch | Fungsi | Aturan |
|---|---|---|
| `main` | Production/stabil. Sumber deploy GCP. | Dilarang commit langsung. Hanya PR dari `dev`. Setiap rilis diberi tag `vMAJOR.MINOR.PATCH`. |
| `dev` | Integrasi FE + BE, diuji lokal. | Dilarang commit langsung. Hanya PR dari branch fitur. |
| `feat/*` `fix/*` `chore/*` | Kerja harian. | Dari `dev`, umur pendek (maks. 2–3 hari), dihapus setelah merge. Contoh: `feat/node-1-gap-analyzer`. |

Merge: feature → `dev` = **squash merge** (judul PR = Conventional Commit). `dev` → `main` = **merge commit** (riwayat rilis tetap utuh).

### 4.2 Branch protection (Settings → Branches) — `main` dan `dev`
- [ ] Require a pull request before merging, **Required approvals = 1**
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require status checks: `Backend — lint & test`, `Docker — build & smoke test`
- [ ] Require branches to be up to date before merging
- [ ] Block force pushes · Restrict deletions
- [ ] `main`: tidak ada bypass. `dev`: tidak ada bypass.

**Peringatan:** di GitHub Free, branch protection pada repo **private** tidak tersedia. Pilihan: (a) repo public, atau (b) aktifkan GitHub Student Developer Pack (Pro). Verifikasi di Settings → Branches sebelum mengandalkan aturan ini. Tanpa proteksi, aturan §0 poin 4 hanya jadi kesepakatan lisan.

**Risiko 2 orang:** approval wajib berarti PR macet bila rekan tidak ada. Sepakati SLA review 24 jam. Menjelang deadline (< 24 jam), pemilik repo boleh menonaktifkan sementara aturan approval, dengan catatan tertulis di PR dan diaktifkan kembali setelah merge.

### 4.3 Kebijakan PR
- PR kecil (idealnya < 400 baris diff), satu tujuan. Template di `.github/pull_request_template.md`.
- Penulis tidak boleh meng-approve PR sendiri (GitHub memang melarang). Reviewer memeriksa: kebenaran logika, aturan Non-LMS, tidak ada secret, test baru untuk perilaku baru, kontrak API tidak berubah diam-diam.
- Review komentar diselesaikan sebelum merge (*Require conversation resolution*).

### 4.4 Conventional Commits

Format: `<tipe>(<scope opsional>): <ringkasan imperatif, huruf kecil, tanpa titik>`

| Tipe | Pakai untuk |
|---|---|
| `feat:` | fitur baru |
| `fix:` | perbaikan bug |
| `docs:` | dokumentasi saja |
| `chore:` | tooling, dependensi, konfigurasi |
| `test:` `refactor:` `ci:` | sesuai namanya |

Contoh: `feat(agents): add gap analyzer node` · `fix(api): reject unknown career enum` · `chore: pin backend dependencies`

**Atomic commit + checkpoint:** satu commit = satu perubahan logis yang bisa di-revert sendiri. `git push` di akhir setiap sesi kerja, termasuk setelah sesi dengan AI coding assistant. Kode yang sudah lolos validasi tapi belum di-push adalah kode yang bisa hilang.

### 4.5 File sensitif
- `.gitignore` sudah memblokir: `.env`, `.env.*` (kecuali `.env.example`), `*.pem`, `*.key`, `id_rsa*`, `service-account*.json`, `node_modules/`, `__pycache__/`, `pgdata/`, dump DB.
- `.env.example` hanya berisi nilai dummy. Variabel baru → tambahkan ke `.env.example` pada PR yang sama.
- Terlanjur commit secret? **Anggap bocor.** Rotasi key dulu, baru bersihkan riwayat. Menghapus file di commit berikutnya tidak menghapus secret dari riwayat.
- Aktifkan GitHub *Secret scanning* dan *Push protection* bila tersedia di plan Anda.

### 4.6 CI — `.github/workflows/ci.yml` (aktif)
Dipicu: PR ke `dev`/`main`, push ke `dev`. Tidak memerlukan secret.

```yaml
name: CI

# Jalan di setiap PR ke dev/main dan setiap push ke dev.
# Tidak butuh secret apa pun: LLM tidak dipanggil di test (wajib di-mock).
on:
  pull_request:
    branches: [dev, main]
  push:
    branches: [dev]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend:
    name: Backend — lint & test
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements*.txt

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Ruff (lint)
        run: ruff check .

      - name: Ruff (format check)
        run: ruff format --check .

      - name: Pytest
        run: pytest

  docker:
    name: Docker — build & smoke test
    runs-on: ubuntu-latest
    needs: backend
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - name: Siapkan .env dummy (bukan secret)
        run: cp .env.example .env

      - name: Validasi compose file
        run: docker compose -f docker-compose.yml config --quiet

      - name: Build & start (tunggu healthcheck)
        run: docker compose -f docker-compose.yml up --build --detach --wait --wait-timeout 120

      - name: Smoke test endpoint
        run: |
          curl --fail --silent --show-error http://127.0.0.1:8000/healthz
          curl --fail --silent --show-error http://127.0.0.1:8000/readyz
          curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/meta/careers

      - name: Dump log kalau gagal
        if: failure()
        run: docker compose -f docker-compose.yml logs --no-color

      - name: Cleanup
        if: always()
        run: docker compose -f docker-compose.yml down --volumes
```

### 4.7 CD — `.github/workflows/cd.yml` (Phase 2, opsional)
Dipicu push ke `main` atau manual. **Tidak berjalan sama sekali** selama repo variable `GCP_ENABLED` bukan `true`; aktifkan setelah VM hidup dan runbook `deploy/README.md` selesai.

```yaml
name: CD (GCP VM)

# PHASE 2 — NONAKTIF sampai repo variable GCP_ENABLED = 'true'.
# Aktifkan HANYA setelah: free credit GCP diklaim, VM hidup, runbook deploy/README.md selesai.
on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: cd-production
  cancel-in-progress: false # jangan batalkan deploy yang sedang berjalan

jobs:
  deploy:
    name: SSH deploy ke Compute Engine
    if: ${{ vars.GCP_ENABLED == 'true' }}
    runs-on: ubuntu-latest
    environment: production
    timeout-minutes: 20
    env:
      VM_IP: ${{ secrets.GCP_VM_IP }}
      VM_USER: ${{ vars.GCP_SSH_USER || 'deploy' }}
      APP_DIR: /opt/learnflow
    steps:
      - uses: actions/checkout@v4

      - name: Siapkan SSH (known_hosts di-pin, bukan ssh-keyscan)
        env:
          SSH_KEY: ${{ secrets.GCP_SSH_KEY }}
          SSH_KNOWN_HOSTS: ${{ secrets.GCP_SSH_KNOWN_HOSTS }}
        run: |
          install -m 700 -d ~/.ssh
          printf '%s\n' "$SSH_KEY" > ~/.ssh/id_deploy
          chmod 600 ~/.ssh/id_deploy
          printf '%s\n' "$SSH_KNOWN_HOSTS" > ~/.ssh/known_hosts

      - name: Tulis .env produksi di VM
        env:
          POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          POSTGRES_USER: ${{ vars.POSTGRES_USER || 'learnflow' }}
          POSTGRES_DB: ${{ vars.POSTGRES_DB || 'learnflow' }}
          LLM_PROVIDER: ${{ vars.LLM_PROVIDER || 'gemini' }}
          CORS_ORIGINS: ${{ vars.CORS_ORIGINS }}
        run: |
          ssh -i ~/.ssh/id_deploy -o IdentitiesOnly=yes "$VM_USER@$VM_IP" \
            "umask 077 && cat > $APP_DIR/.env" <<EOF
          APP_ENV=production
          LOG_LEVEL=info
          CORS_ORIGINS=$CORS_ORIGINS
          POSTGRES_USER=$POSTGRES_USER
          POSTGRES_PASSWORD=$POSTGRES_PASSWORD
          POSTGRES_DB=$POSTGRES_DB
          LLM_PROVIDER=$LLM_PROVIDER
          LLM_API_KEY=$LLM_API_KEY
          EOF

      - name: Pull kode & jalankan deploy script
        run: |
          ssh -i ~/.ssh/id_deploy -o IdentitiesOnly=yes "$VM_USER@$VM_IP" \
            "cd $APP_DIR && git fetch --prune origin main && git reset --hard origin/main && bash deploy/deploy.sh"
```

### 4.8 Manajemen kredensial — GitHub Repository Secrets

| Nama | Tipe | Dipakai oleh | Catatan |
|---|---|---|---|
| `GCP_SSH_KEY` | Secret | CD | Private key ed25519 khusus deploy; bukan key pribadi |
| `GCP_VM_IP` | Secret | CD | IP publik VM |
| `GCP_SSH_KNOWN_HOSTS` | Secret | CD | Host key VM yang diverifikasi manual (mencegah MITM; jangan `ssh-keyscan` otomatis di pipeline) |
| `POSTGRES_PASSWORD` | Secret | CD → `.env` VM | `openssl rand -hex 24` (alfanumerik) |
| `LLM_API_KEY` | Secret | CD → `.env` VM | CI **tidak** memakainya |
| `GCP_ENABLED` | Variable | CD | Saklar utama; default kosong = CD mati |
| `CORS_ORIGINS`, `GCP_SSH_USER`, `LLM_PROVIDER` | Variable | CD | Bukan rahasia |

Prinsip: secret hanya masuk `.env` di VM (permission 600), tidak masuk image, tidak ikut `COPY`, tidak di-log.

---

## 5. Kontrak API & Data (Frontend ↔ Backend)

> Status: **usulan**, dibekukan Senin 26 Okt (tugas Anggota 2). Perubahan setelahnya = PR kontrak, di-approve dua orang.

### 5.1 Endpoint

| Method | Path | Status | Keterangan |
|---|---|---|---|
| GET | `/healthz` · `/readyz` | ✅ ada | Liveness · readiness (cek DB) |
| GET | `/api/v1/meta/careers` | ✅ ada | `{"careers": [...3 role], "count": 3}` |
| GET | `/api/v1/meta/courses` | ⏳ W2 | `{"courses": [{"code": "0072", "name": "Algoritma", "semester": 2}]}` |
| POST | `/api/v1/roadmaps` | ⏳ W4 | Buat task. `202` → `{"task_id": "<uuid>", "status": "queued"}`. `422` input salah (Node 0). `429` kena rate limit. |
| GET | `/api/v1/roadmaps/{task_id}` | ⏳ W4 | Polling: `{"task_id", "status", "progress", "result"}` |
| GET | `/api/v1/roadmaps/{task_id}/stream` | ⏳ W4 | SSE |

Alasan POST dan stream dipisah: `EventSource` di browser hanya mendukung GET.

**Body `POST /roadmaps`**
```json
{
  "semester": 5,
  "target_career": "Backend Developer",
  "completed_course_codes": ["0072", "0001"]
}
```
Aturan: `target_career` ∈ enum `CareerTrack`; `semester` 1–14; `completed_course_codes` 1–80 item, pola `^[0-9]{4}$` *(asumsi format kode MK; sesuaikan dengan kode riil kampus)*, harus ada di `courses.json`. Nama pengguna tidak dikumpulkan di V1 (kurangi data pribadi); tabel `users` baru dipakai bila ada kebutuhan simpan profil.

### 5.2 Status task
`queued` → `running` → `done` | `failed` | `fallback` (selesai memakai Fallback Template).

### 5.3 Event SSE
| Event | `data` | Kapan |
|---|---|---|
| `progress` | `{"node": "node_0..node_3", "loop_counter": 0}` | Tiap node mulai/selesai |
| `result` | objek hasil §5.4 | Sekali, akhir sukses atau fallback |
| `error` | `{"code": "LLM_TIMEOUT", "message": "..."}` | Gagal total |
| komentar `: ping` | — | Tiap 15 dtk (jaga koneksi) |

### 5.4 Objek hasil (menyempurnakan blueprint §7)
```json
{
  "career_track": "Backend Developer",
  "is_fallback": false,
  "roadmap_graph": {
    "nodes": [
      { "id": "n1", "label": "0072 - Algoritma", "source": "Kampus", "status": "DONE" },
      { "id": "n3", "label": "Docker Basics", "source": "Eksternal", "status": "RECOMMENDED_NOW" },
      { "id": "n4", "label": "Relational Database Certification", "source": "Sertifikasi_Gratis", "status": "RECOMMENDED_NOW",
        "cert": { "id": "fcc-relational-database", "provider": "FreeCodeCamp", "search_query": "freeCodeCamp Relational Database certification" } },
      { "id": "n9", "label": "AWS Certified Developer - Associate", "source": "Sertifikasi_Berbayar", "status": "UPCOMING",
        "cert": { "id": "aws-developer-associate", "provider": "AWS", "search_query": "AWS Certified Developer Associate exam guide" } }
    ],
    "edges": [
      { "from": "n1", "to": "n3", "type": "prerequisite" },
      { "from": "n4", "to": "n9", "type": "prerequisite" }
    ]
  }
}
```
Enum: `source` ∈ `Kampus | Eksternal | Sertifikasi_Gratis | Sertifikasi_Berbayar` · `status` ∈ `DONE | RECOMMENDED_NOW | UPCOMING` *(`UPCOMING` = tambahan dari blueprint)* · `edge.type` = `prerequisite`. `cert` hanya ada pada node sertifikasi dan tidak pernah memuat harga atau URL.

### 5.5 Format error (semua endpoint)
`{"detail": "<pesan>"}` (default FastAPI untuk 4xx). Rate limit `429` menyertakan header `Retry-After`.

### 5.6 Tabel tambahan: `roadmap_tasks`
`id` UUID PK (= `task_id`) · `status` text · `progress` JSONB · `result` JSONB null · `error` text null · `created_at` timestamptz · `updated_at` timestamptz. Alasan: polling dan SSE butuh state yang bertahan antar request; in-memory dict hilang saat container restart.

---

## 6. Keputusan Arsitektur & Risiko

| # | Risiko / keputusan | Dampak | Mitigasi |
|---|---|---|---|
| 1 | **Data kurikulum kampus belum ada di repo.** Diferensiasi utama (kode MK riil) bergantung padanya. | Node 1 tidak bisa dibangun | Kumpulkan daftar MK (kode, nama, semester) + peta ke skill tag paling lambat W2. Tanpa ini W3 mundur. |
| 2 | Kuota/latensi LLM gratis | Demo gagal saat presentasi | `FakeLLMProvider` untuk test, Fallback Template, timeout + retry terbatas, uji demo dengan LLM mati |
| 3 | Free credit GCP tidak aktif tepat waktu | Phase 2 tidak tercapai | Gate 16 Nov + Plan B §3.2 |
| 4 | Judul/status gratis program sertifikasi berubah | Rekomendasi usang | Hanya `search_query`, disclaimer di UI, `last_reviewed`, review bulanan |
| 5 | Scope creep ke LMS | Menyalahi konstrain proyek | Aturan Emas #1 + checklist PR |
| 6 | Nginx mem-buffer SSE | Progres tidak tampil sampai selesai | `proxy_buffering off` (sudah di `deploy/nginx/learnflow.conf`), fallback polling di frontend |
| 7 | Rate limit slowapi in-memory per proses | Multi-worker melewati batas | V1 pakai 1 worker; Redis di V2 |
| 8 | `X-Forwarded-For` bisa dipalsukan | Bypass rate limit | Port backend hanya di `127.0.0.1`; Nginx menimpa header |
| 9 | LLM menulis harga/link | Melanggar aturan modul | Whitelist ID + scrub regex (§1.4) |
| 10 | Approval wajib vs 2 orang | PR macet | SLA 24 jam + prosedur darurat §4.2 |
| 11 | Dependensi belum di-pin persis | Build tidak reproducible | Setelah W1 lolos lokal: `pip freeze` → pin versi di `requirements.txt` (ubah `>=,<` menjadi `==`) |

---

## 7. Definition of Done per PR
- [ ] CI hijau (lint, format, test, build Docker)
- [ ] Berjalan lewat `docker compose up --build` di laptop penulis
- [ ] Tidak ada secret, `.env`, atau data pribadi di diff
- [ ] Test baru untuk perilaku baru; LLM di-mock
- [ ] Kontrak §5 diperbarui bila berubah
- [ ] Tidak menambah fitur LMS
- [ ] 1 approval dari rekan, semua komentar selesai
