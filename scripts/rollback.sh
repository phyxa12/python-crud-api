#!/usr/bin/env bash
set -u

CONTAINER_NAME=${CONTAINER_NAME:-production-api-container}
VOLUME_NAME=${VOLUME_NAME:-production-api-data}
PORT_MAPPING=${PORT_MAPPING:-5000:5000}
DATA_PATH=${DATA_PATH:-/var/lib/backend_data}
MARKER=${MARKER:-.deploy/previous_image.txt}

if [ ! -s "$MARKER" ]; then
    echo "No previous image recorded at $MARKER, rollback skipped."
    exit 0
fi

PREVIOUS=$(cat "$MARKER")

if ! docker image inspect "$PREVIOUS" >/dev/null 2>&1; then
    echo "Previous image $PREVIOUS is not available locally, rollback skipped."
    exit 0
fi

echo "Rolling back container to $PREVIOUS"
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker volume create "$VOLUME_NAME" >/dev/null
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT_MAPPING" \
    -v "$VOLUME_NAME:$DATA_PATH" \
    --restart unless-stopped \
    "$PREVIOUS"

echo "Rollback finished, container now runs $PREVIOUS"
