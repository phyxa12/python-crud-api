# Jenkins lab image dan inisialisasi otomatis

Folder ini berisi image Jenkins yang sudah memiliki Docker CLI, Python 3, dan ruff, plus
skrip `init.groovy.d` untuk menyiapkan instance tanpa wizard interaktif.

## Build image

```bash
docker build -t jenkins-lab:lts -f jenkins/Dockerfile jenkins/
```

## Jalankan dengan inisialisasi otomatis

`job.xml` masih memakai `USERNAME`; ganti dengan akun GitHub Anda sebelum dipakai.

```bash
export JENKINS_ADMIN_PASSWORD='<password-kuat>'
export JENKINS_WEBHOOK_SECRET='<secret-acak>'

docker network create jenkins-net
docker volume create jenkins-data

docker run -d --name jenkins-server --network jenkins-net \
  -p 8081:8080 -p 50000:50000 \
  --add-host=host.docker.internal:host-gateway \
  -v jenkins-data:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/jenkins/init.groovy.d:/var/jenkins_home/init.groovy.d" \
  -v "$HOME/.ssh/deploy_key:/run/secrets/deploy_key:ro" \
  -v "$PWD/jenkins/init.groovy.d/job.xml:/run/config/job.xml:ro" \
  -e JENKINS_ADMIN_PASSWORD \
  -e JENKINS_WEBHOOK_SECRET \
  -e HEALTH_URL=http://host.docker.internal:5000/health \
  -e JAVA_OPTS='-Djenkins.install.runSetupWizard=false' \
  --group-add 0 \
  jenkins-lab:lts
```

Catatan:

- `--group-add 0` diperlukan agar user `jenkins` dapat menulis ke Docker socket pada
  Docker Desktop. Ini hanya untuk lab; pada produksi gunakan agent terpisah.
- `HEALTH_URL` dipakai stage health check karena `localhost` di dalam container Jenkins
  bukan host.
- Deploy key read-only dibuat dengan `ssh-keygen -t ed25519` lalu ditambahkan lewat
  `gh repo deploy-key add <key>.pub --repo OWNER/REPO`.
- Jangan pernah menaruh password, secret, atau private key di repository.
- Jika tidak ingin memakai init script, cukup jalankan container tanpa mount
  `init.groovy.d` dan ikuti wizard pada `http://localhost:8081`.
