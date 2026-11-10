#!/usr/bin/env bash
# Ejecutar SOLO en la instancia Ubuntu acordada y después de autorizar sus cambios.
# No contiene credenciales ni crea recursos AWS. Instala Docker y arranca el servicio.
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[a-z0-9][a-z0-9_-]*/[a-z0-9][a-z0-9._-]*(:[a-zA-Z0-9._-]+|@sha256:[a-f0-9]{64})$ ]]; then
  echo "Uso: sudo bash deploy/ec2-bootstrap.sh USUARIO/stock-market:1.0" >&2
  exit 2
fi
IMAGE_REF="$1"
if [[ "$EUID" -ne 0 ]]; then
  echo "Ejecuta con sudo en la instancia EC2 Ubuntu autorizada." >&2
  exit 2
fi
. /etc/os-release
if [[ "$ID" != ubuntu || "$(dpkg --print-architecture)" != amd64 ]]; then
  echo "Este despliegue requiere Ubuntu amd64, igual que la imagen local." >&2
  exit 2
fi
if command -v docker >/dev/null && docker container inspect taller1-stock-market >/dev/null 2>&1; then
  echo "Ya existe taller1-stock-market; no se reemplazará ni eliminará automáticamente." >&2
  exit 2
fi

if ! command -v docker >/dev/null; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' \
    "$(dpkg --print-architecture)" "$VERSION_CODENAME" > /etc/apt/sources.list.d/docker.list
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io
fi
systemctl enable --now docker
docker pull "$IMAGE_REF"
docker run -d --name taller1-stock-market \
  --restart unless-stopped \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --memory 768m --cpus 1 --pids-limit 128 \
  --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 \
  -p 80:5000 "$IMAGE_REF"

for attempt in {1..30}; do
  if docker exec taller1-stock-market python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"; then
    echo "Servicio disponible localmente en HTTP/80. Verifica ahora desde Ubuntu local."
    exit 0
  fi
  sleep 2
done
docker logs --tail 50 taller1-stock-market
echo "La comprobación local falló. El contenedor se conserva para diagnóstico." >&2
exit 1
