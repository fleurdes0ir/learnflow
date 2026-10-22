## Apa yang berubah
<!-- 1–3 kalimat. Kenapa, bukan cuma apa. -->

## Tipe
- [ ] feat
- [ ] fix
- [ ] chore / docs / ci

## Checklist (wajib sebelum minta review)
- [ ] Branch dari `dev` dan nama sesuai `feat/*`, `fix/*`, `chore/*`
- [ ] Commit mengikuti Conventional Commits
- [ ] `ruff check .` + `ruff format --check .` + `pytest` lolos lokal
- [ ] `docker compose up --build` jalan di laptop sendiri
- [ ] Tidak ada secret / `.env` / API key di diff
- [ ] Tidak ada fitur LMS (materi, kuis, video, tugas) — LearnFlow BUKAN LMS
- [ ] Kalau menyentuh kontrak API: `docs/TEAM_WORKFLOW.md` §5 sudah diperbarui

## Cara tes
<!-- Perintah / langkah yang reviewer bisa jalankan -->
