"""Rate limiter (slowapi). Dipakai endpoint generate roadmap mulai Milestone 1."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Storage in-memory = counter PER PROSES. Jalankan 1 worker uvicorn di V1.
# Multi-worker / multi-instance butuh storage Redis (V2).
# Di belakang Nginx: Dockerfile sudah memakai --proxy-headers; Nginx meng-overwrite
# X-Forwarded-For (deploy/nginx/learnflow.conf) sehingga IP tidak bisa dipalsukan klien.
limiter = Limiter(key_func=get_remote_address)
