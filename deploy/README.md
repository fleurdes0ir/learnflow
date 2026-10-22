# deploy/ — Phase 2 (GCP Compute Engine)

> **Jangan disentuh sebelum Phase 1 (local Docker Compose) lolos dan free credit GCP sudah aktif.**
> Semua file di sini belum pernah diuji di VM nyata — anggap draf sampai deploy pertama berhasil.

## Isi
| File | Fungsi |
|---|---|
| `deploy.sh` | Dijalankan di VM: `docker compose -f docker-compose.yml up -d --build --wait` + cek `/healthz` |
| `nginx/learnflow.conf` | Reverse proxy host-level (80/443), SSE-safe, anti-spoof `X-Forwarded-For` |

## Runbook bootstrap VM (sekali jalan)
```bash
# 1. VM: Debian/Ubuntu, e2-small atau lebih, firewall publik HANYA 22/80/443.
# 2. Install Docker + Compose plugin + Nginx + Git (ikuti docs resmi Docker untuk distro VM).
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/learnflow && sudo chown deploy:deploy /opt/learnflow

# 3. Sebagai user deploy: clone repo (repo private → pakai read-only deploy key GitHub).
sudo -iu deploy git clone git@github.com:<org-atau-user>/learnflow.git /opt/learnflow

# 4. Nginx
sudo cp /opt/learnflow/deploy/nginx/learnflow.conf /etc/nginx/conf.d/learnflow.conf
sudo nginx -t && sudo systemctl reload nginx
```

## Aktivasi CD
1. Buat SSH keypair khusus deploy (`ssh-keygen -t ed25519 -f gcp_deploy -N ""`), pasang `.pub` di `~deploy/.ssh/authorized_keys`.
2. GitHub → *Settings → Secrets and variables → Actions*:

| Tipe | Nama | Isi |
|---|---|---|
| Secret | `GCP_SSH_KEY` | isi private key `gcp_deploy` |
| Secret | `GCP_VM_IP` | IP publik VM |
| Secret | `GCP_SSH_KNOWN_HOSTS` | output `ssh-keyscan -t ed25519 <IP>` yang diverifikasi manual |
| Secret | `POSTGRES_PASSWORD` | `openssl rand -hex 24` (alfanumerik, aman untuk `.env`) |
| Secret | `LLM_API_KEY` | API key provider LLM |
| Variable | `GCP_ENABLED` | `true` (saklar utama CD) |
| Variable | `CORS_ORIGINS` | `http://<IP-atau-domain>` |

3. Hapus file `gcp_deploy` dari laptop setelah di-upload ke Secrets.
