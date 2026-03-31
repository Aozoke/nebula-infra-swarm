#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1}"
STACK_NAME="${STACK_NAME:-nebula}"

echo "== Node status =="
docker node ls

echo
echo "== Stack services =="
docker stack services "${STACK_NAME}"

echo
echo "== Smoke flow (users -> posts -> feed) =="
HANDLE="smoke-$(date +%s)"
USER_RESP="$(curl -sS -X POST "${BASE_URL}/users" -H 'Content-Type: application/json' -d "{\"handle\":\"${HANDLE}\"}")"
USER_ID="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("id",""))' <<<"${USER_RESP}")"
if [[ -z "${USER_ID}" ]]; then
  echo "Error: failed to create user. Response: ${USER_RESP}"
  exit 1
fi
echo "Created user: ${USER_ID}"

POST_RESP="$(curl -sS -X POST "${BASE_URL}/posts" -H 'Content-Type: application/json' -d "{\"author_id\":\"${USER_ID}\",\"content\":\"smoke post\"}")"
POST_ID="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("id",""))' <<<"${POST_RESP}")"
if [[ -z "${POST_ID}" ]]; then
  echo "Error: failed to create post. Response: ${POST_RESP}"
  exit 1
fi
echo "Created post: ${POST_ID}"

sleep 2
FEED_RESP="$(curl -sS "${BASE_URL}/feed/${USER_ID}")"
python3 - "$POST_ID" <<'PY' <<<"${FEED_RESP}"
import json
import sys

post_id = sys.argv[1]
payload = json.loads(sys.stdin.read())
items = payload.get("items", [])
if not any(item.get("post_id") == post_id for item in items):
    print("Error: post not found in feed payload")
    print(json.dumps(payload, indent=2))
    sys.exit(1)
print("Feed check OK: post found in feed")
PY

echo
echo "All smoke checks passed."
