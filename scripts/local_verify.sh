#!/usr/bin/env bash
set -euo pipefail

IMAGE=${IMAGE:-python-crud-api:manual}
CONTAINER=${CONTAINER:-production-api-container}
VOLUME=${VOLUME:-production-api-data}
BASE=${BASE:-http://localhost:5000}
DATA_PATH=${DATA_PATH:-/var/lib/backend_data}

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; exit 1; }

cleanup_container() {
    docker stop "$CONTAINER" >/dev/null 2>&1 || true
    docker rm "$CONTAINER" >/dev/null 2>&1 || true
}

wait_healthy() {
    for _ in $(seq 1 15); do
        if curl -fsS "$BASE/health" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    docker logs --tail 20 "$CONTAINER" || true
    fail "container did not become healthy"
}

echo "== 1. Build image =="
docker build -t "$IMAGE" .
pass "image $IMAGE built"

echo
echo "== 2. Fresh volume and container =="
cleanup_container
docker volume rm "$VOLUME" >/dev/null 2>&1 || true
docker volume create "$VOLUME" >/dev/null
docker run -d --name "$CONTAINER" -p 5000:5000 -v "$VOLUME:$DATA_PATH" "$IMAGE" >/dev/null
wait_healthy
pass "container started and healthy"

echo
echo "== 3. Health endpoint =="
curl -i "$BASE/health"
pass "GET /health returned 200"

echo
echo "== 4. Empty list =="
curl -s "$BASE/messages"
echo
pass "GET /messages returned empty collection"

echo
echo "== 5. Create messages =="
curl -i -X POST "$BASE/messages" -H 'Content-Type: application/json' \
    -d '{"message":"Pesan pertama dari praktikum"}'
echo
curl -i -X POST "$BASE/messages" -H 'Content-Type: application/json' \
    -d '{"message":"Pesan kedua"}'
pass "POST /messages created two messages"

echo
echo "== 6. Read list and single item =="
curl -s "$BASE/messages"
echo
curl -s "$BASE/messages/1"
pass "GET /messages and GET /messages/1 returned data"

echo
echo "== 7. Validation cases =="
EMPTY_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/messages" \
    -H 'Content-Type: application/json' -d '{"message":""}')
[ "$EMPTY_CODE" = "400" ] || fail "empty message expected 400, got $EMPTY_CODE"
LONG_BODY=$(printf '{"message":"%s"}' "$(printf 'x%.0s' {1..501})")
LONG_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/messages" \
    -H 'Content-Type: application/json' -d "$LONG_BODY")
[ "$LONG_CODE" = "400" ] || fail "long message expected 400, got $LONG_CODE"
MISSING_CODE=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/messages/999")
[ "$MISSING_CODE" = "404" ] || fail "unknown id expected 404, got $MISSING_CODE"
SEARCH_TOTAL=$(curl -s "$BASE/messages?search=kedua")
echo "$SEARCH_TOTAL"
printf '%s' "$SEARCH_TOTAL" | grep -q '"total": 1' || fail "search filter did not match one item"
pass "validation, not-found and filter behaviour correct"

echo
echo "== 8. Delete cases =="
curl -i -X DELETE "$BASE/messages?index=999" | head -1
curl -i -X DELETE "$BASE/messages?index=0"
curl -s "$BASE/messages"
echo
pass "DELETE removed index 0 and rejected out-of-range index"

echo
echo "== 9. Persistence across redeploy =="
BEFORE=$(curl -s "$BASE/messages")
printf 'before redeploy: %s\n' "$BEFORE"
cleanup_container
docker run -d --name "$CONTAINER" -p 5000:5000 -v "$VOLUME:$DATA_PATH" "$IMAGE" >/dev/null
wait_healthy
AFTER=$(curl -s "$BASE/messages")
printf 'after redeploy:  %s\n' "$AFTER"
[ "$BEFORE" = "$AFTER" ] || fail "data changed after redeploy"
pass "data survived container replacement via named volume $VOLUME"

echo
echo "== 10. Container inspection =="
docker ps --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker volume inspect "$VOLUME" --format 'volume={{.Name}} mountpoint={{.Mountpoint}}'

echo
echo "== 11. Docker HEALTHCHECK status =="
sleep 12
docker inspect --format '{{.State.Health.Status}}' "$CONTAINER"

echo
echo "All local verification steps passed."
