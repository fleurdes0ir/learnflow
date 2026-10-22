# knowledge_base/

Data statis (JSON) yang dibaca backend. **Bukan** konten belajar — LearnFlow bukan LMS.

| File | Status | Isi |
|---|---|---|
| `certifications.json` | ✅ ada | Rekomendasi sertifikasi per karier. Free dulu, paid belakangan. |
| `backend_req.json` | ⏳ Milestone 1 (Anggota 2) | Benchmark kompetensi + kode MK kampus untuk Node 1 (Gap Analyzer) |
| `data_scientist_req.json` | ⏳ Milestone 1 | idem |
| `devops_req.json` | ⏳ Milestone 1 | idem |
| `fallback_template.json` | ⏳ Milestone 1 | Roadmap statis untuk Node 3 saat `loop_counter >= 3` |

## Aturan `certifications.json` (dijaga `backend/tests/test_knowledge_base.py`)

1. Urutan key per role: `free_options` **harus** sebelum `paid_options`; `free_options` tidak boleh kosong.
2. Provider gratis: FreeCodeCamp, Kaggle, Cisco Networking Academy, Google Cloud Skills Boost, Microsoft Applied Skills.
3. Provider berbayar: AWS, Oracle, CNCF / Linux Foundation (CKA), CompTIA.
4. **Dilarang**: harga/nominal, field `price`, field `url`, string `http(s)://` atau `www.`.
5. Satu-satunya cara menunjuk sumber: `search_query` (string pencarian, bukan link).
6. Setiap entri punya persis key: `id, provider, title, level, skills, prerequisite_skills, search_query`.
7. `id` unik di seluruh file. Role harus persis sama dengan enum `CareerTrack`.

Judul program pihak ketiga bisa berubah. Review manual tiap bulan, lalu update `last_reviewed`.
