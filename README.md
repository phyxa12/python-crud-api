# python-crud-api

Python REST API sederhana untuk praktikum CI/CD (Jenkins + GitHub + Docker + ngrok).
Aplikasi menyimpan pesan pada file JSON di dalam direktori yang dipasang ke Docker named
volume, sehingga data bertahan ketika container diganti.

## Struktur proyek

| File | Fungsi |
| --- | --- |
| `app.py` | REST API tanpa dependency eksternal (`http.server`) |
| `test_app.py` | 14 unit/integration test untuk endpoint dan persistence |
| `Dockerfile` | Image `python:3.11-slim` + `HEALTHCHECK` |
| `.dockerignore` | Mencegah Git, test, dan cache ikut ke build context |
| `Jenkinsfile` | Pipeline-as-code: checkout, lint, test, build, deploy, health check, rollback |
| `scripts/rollback.sh` | Rollback ke image yang berjalan sebelum deployment gagal |
| `scripts/local_verify.sh` | Verifikasi lokal end-to-end (build, CRUD, persistence) |
| `jenkins/Dockerfile` | Image Jenkins lab: Docker CLI, Python, ruff, plugin pipeline |
| `jenkins/plugins.txt` | Daftar plugin yang dipasang otomatis |
| `LAPORAN.md` | Laporan praktikum, jawaban pertanyaan analisis, dan daftar bukti |
| `Bukti/` | Log bukti eksekusi nyata (test, verifikasi lokal, build Jenkins) |

## Endpoint

| Method | Path | Keterangan |
| --- | --- | --- |
| GET | `/health` | Health check, mengembalikan `{"status": "active"}` |
| GET | `/messages` | Daftar pesan; mendukung `?search=<kata>` dan `?limit=<n>` |
| GET | `/messages/{id}` | Detail satu pesan berdasarkan id |
| POST | `/messages` | Membuat pesan; body `{"message": "..."}`, maksimal 500 karakter |
| DELETE | `/messages?index=<n>` | Menghapus pesan berdasarkan posisi pada daftar |

Contoh:

```bash
curl -i http://localhost:5000/health
curl -s http://localhost:5000/messages
curl -i -X POST http://localhost:5000/messages \
  -H 'Content-Type: application/json' \
  -d '{"message":"Pesan pertama dari praktikum"}'
curl -s http://localhost:5000/messages/1
curl -s 'http://localhost:5000/messages?search=pertama'
curl -i -X DELETE 'http://localhost:5000/messages?index=0'
```

## Menjalankan tanpa Docker

```bash
python3 app.py
# terminal lain
curl -i http://localhost:5000/health
```

Variabel `DATA_FILE` dapat dioverride, misalnya `DATA_FILE=/tmp/messages.json python3 app.py`.

## Test dan lint

```bash
python3 -m ruff check app.py test_app.py
python3 -m py_compile app.py test_app.py
python3 -m unittest -v test_app.py
```

`requirements-dev.txt` hanya berisi tool pengembangan (`ruff`); aplikasi sendiri tidak
membutuhkan dependency eksternal.

## Menjalankan di Docker

```bash
docker build -t python-crud-api:manual .
docker volume create production-api-data
docker run -d --name production-api-container \
  -p 5000:5000 \
  -v production-api-data:/var/lib/backend_data \
  python-crud-api:manual

curl -i http://localhost:5000/health
docker inspect --format '{{.State.Health.Status}}' production-api-container
```

Verifikasi end-to-end (termasuk bukti persistence setelah redeploy):

```bash
bash scripts/local_verify.sh
```

## Jenkins

### 1. Jalankan Jenkins dengan Docker CLI

Image `jenkins/jenkins:lts-jdk17` belum memiliki Docker CLI maupun Python, sehingga
`jenkins/Dockerfile` menambahkan keduanya sekaligus memasang plugin pipeline.

```bash
docker network create jenkins-net
docker volume create jenkins-data
docker build -t jenkins-lab:lts -f jenkins/Dockerfile jenkins/

docker run -d \
  --name jenkins-server \
  --network jenkins-net \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins-data:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --restart unless-stopped \
  jenkins-lab:lts

docker exec jenkins-server cat /var/jenkins_home/secrets/initialAdminPassword
```

Catatan platform:

- Linux: mount socket seperti di atas sudah cukup.
- macOS/Windows dengan Docker Desktop: mount socket `/var/run/docker.sock` tetap bekerja,
  tetapi jangan memount binary Docker host (`-v "$(which docker)"`) karena path host tidak
  valid di dalam container. Gunakan Docker CLI yang sudah dipasang pada image lab.

Verifikasi:

```bash
docker exec jenkins-server docker version
docker exec jenkins-server python3 --version
docker exec jenkins-server python3 -m ruff --version
```

### 2. Kredensial checkout

Pilihan yang dipakai pada praktikum ini: **deploy key read-only** (akses baca hanya ke satu
repository, tanpa hak tulis) dengan kind `SSH Username with private key`, ID
`github-deploy-readonly`.

Pilihan sesuai panduan: **fine-grained PAT** read-only dengan kind `Username with password`,
ID `github-pat-readonly`, permission `Contents: Read-only` + `Metadata: Read-only`,
repository access `Only select repositories`.

Jangan pernah menaruh token di URL repository, `Jenkinsfile`, README, atau screenshot.

### 3. Job pipeline

1. `New Item` -> nama `python-crud-api-pipeline` -> tipe `Pipeline`.
2. `Build Triggers` -> centang **dua** opsi:
   - `GitHub hook trigger for GITScm polling`
   - `Poll SCM` dengan jadwal mis. `H/5 * * * *`

   Keduanya diperlukan. Pada Jenkins modern, handler webhook GitHub hanya "memoking"
   polling SCM milik job; jika job tidak punya trigger `Poll SCM`, poke tersebut tidak
   menghasilkan build (endpoint `/poll` bahkan 404). Ini teramati langsung saat praktikum.
3. `Pipeline` -> `Pipeline script from SCM`, SCM `Git`.
4. Isi `Repository URL`, pilih `Credentials`, `Branch Specifier` = `*/main`,
   `Script Path` = `Jenkinsfile`.
5. `Save`, lalu `Build Now` untuk validasi pertama.

Jika Jenkins berjalan di dalam container, health check harus menargetkan host, bukan
`localhost` milik container Jenkins:

```bash
docker run ... \
  --add-host=host.docker.internal:host-gateway \
  -e HEALTH_URL=http://host.docker.internal:5000/health \
  ...
```

`Jenkinsfile` memakai `${HEALTH_URL:-http://localhost:5000/health}`, sehingga default
panduan tetap berlaku ketika Jenkins berjalan langsung di host.

Skrip inisialisasi otomatis (admin, credential, job) tersedia pada `jenkins/init.groovy.d/`
dan dapat dipasang ke `/var/jenkins_home/init.groovy.d` bila tidak ingin mengisi form UI.

### 4. Webhook lewat ngrok

```bash
ngrok config add-authtoken "<NGROK_AUTHTOKEN>"
ngrok http 8080     # sesuaikan dengan port host Jenkins, mis. 8081 pada lab ini
```

Di GitHub: `Settings` -> `Webhooks` -> `Add webhook`.

- Payload URL: `https://<domain-ngrok>/github-webhook/` (harus berakhir `/github-webhook/`)
- Content type: `application/json`
- Secret: isi dengan nilai acak dan simpan sebagai Jenkins credential (`Secret text`,
  ID `github-webhook-secret`), jangan pernah ditulis di repository
- Event: `Just the push event`

Uji dengan push kecil ke `main`; build harus terpicu tanpa `Build Now`.

Alternatif tanpa akun ngrok: `cloudflared tunnel --url http://localhost:8081` pada Cloudflare
memberi URL HTTPS sementara dengan perilaku yang sama (dipakai untuk membuktikan webhook pada
praktikum ini karena ngrok mewajibkan authtoken).

## Tahap pipeline

| Stage | Isi |
| --- | --- |
| 1. Checkout Code | `checkout scm`, mencatat commit SHA |
| 2. Lint Python | `ruff check app.py test_app.py` |
| 3. Syntax Check & Unit Test | `py_compile` + 14 unit test |
| 4. Build Docker Image | Tag `BUILD_NUMBER` dan commit SHA pendek, plus `latest` |
| 5. Automated Deployment | Simpan image sebelumnya, replace container, volume tetap |
| 6. Health Check | Retry `curl` maksimal 15 kali |
| post failure | `scripts/rollback.sh` mengembalikan container ke image sebelumnya |

## Troubleshooting singkat

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `docker: command not found` | Docker CLI tidak ada di agent | Pakai `jenkins/Dockerfile` pada repo ini |
| `Cannot connect to the Docker daemon` | Socket tidak terpasang | Mount `/var/run/docker.sock`, cek `docker exec jenkins-server docker ps` |
| Webhook tidak memicu job | Tunnel mati / URL salah | Pastikan ngrok aktif dan path `/github-webhook/` |
| Port 5000 sudah dipakai | Container lain | `docker ps`, hentikan container konflik atau ubah `PORT_MAPPING` |
| Pesan hilang setelah redeploy | Volume salah path | Pastikan `-v production-api-data:/var/lib/backend_data` |
| Health check gagal | Container crash | `docker logs production-api-container` |
| Log Python terlambat | Buffering stdout | `PYTHONUNBUFFERED=1` sudah diset pada image |

Dokumentasi lengkap, jawaban pertanyaan analisis, dan daftar bukti ada di `LAPORAN.md`.

<!-- webhook test: 2026-10-31T18:30:51.9164688+07:00 -->
<!-- webhook test 2: 2026-10-31T18:36:19.2531122+07:00 -->
