#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-nebula}"
BASE_URL="${BASE_URL:-http://127.0.0.1}"
OUT_ROOT="${OUT_ROOT:-docs/evidence}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${OUT_ROOT}/${TIMESTAMP}"

if [[ "$(docker info --format '{{.Swarm.ControlAvailable}}')" != "true" ]]; then
  echo "Error: run this script on a Swarm manager node."
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "== Freeze evidence to ${OUT_DIR} =="

docker node ls > "${OUT_DIR}/01-docker-node-ls.txt"
docker stack services "${STACK_NAME}" > "${OUT_DIR}/02-docker-stack-services-${STACK_NAME}.txt"

for service in edge-proxy users-api posts-api feed-api feed-worker postgres redis; do
  docker service ps --no-trunc "${STACK_NAME}_${service}" > "${OUT_DIR}/03-docker-service-ps-${service}.txt" 2>&1 || true
done

for service in edge-proxy users-api posts-api feed-api feed-worker; do
  docker service logs --tail 80 "${STACK_NAME}_${service}" > "${OUT_DIR}/04-docker-service-logs-${service}.txt" 2>&1 || true
done

curl -sS -i "${BASE_URL}/health" > "${OUT_DIR}/10-curl-health.txt"

HANDLE="evidence-$(date +%s)"
USER_RESPONSE="$(curl -sS -i -X POST "${BASE_URL}/users" -H 'Content-Type: application/json' -d "{\"handle\":\"${HANDLE}\"}")"
printf '%s\n' "${USER_RESPONSE}" > "${OUT_DIR}/11-curl-create-user.txt"
USER_BODY="$(printf '%s\n' "${USER_RESPONSE}" | sed -n '/^\r*$/,$p' | sed '1d')"
USER_ID="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("id",""))' <<<"${USER_BODY}")"

if [[ -z "${USER_ID}" ]]; then
  echo "Error: failed to parse created user id. See ${OUT_DIR}/11-curl-create-user.txt"
  exit 1
fi

POST_RESPONSE="$(curl -sS -i -X POST "${BASE_URL}/posts" -H 'Content-Type: application/json' -d "{\"author_id\":\"${USER_ID}\",\"content\":\"evidence post ${TIMESTAMP}\"}")"
printf '%s\n' "${POST_RESPONSE}" > "${OUT_DIR}/12-curl-create-post.txt"
POST_BODY="$(printf '%s\n' "${POST_RESPONSE}" | sed -n '/^\r*$/,$p' | sed '1d')"
POST_ID="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("id",""))' <<<"${POST_BODY}")"

if [[ -z "${POST_ID}" ]]; then
  echo "Error: failed to parse created post id. See ${OUT_DIR}/12-curl-create-post.txt"
  exit 1
fi

sleep 2
curl -sS -i "${BASE_URL}/feed/${USER_ID}" > "${OUT_DIR}/13-curl-feed.txt"

cat > "${OUT_DIR}/00-summary.txt" <<EOF
Nebula evidence freeze
timestamp_utc=${TIMESTAMP}
stack_name=${STACK_NAME}
base_url=${BASE_URL}
created_user_handle=${HANDLE}
created_user_id=${USER_ID}
created_post_id=${POST_ID}
EOF

echo "Evidence captured:"
echo "  ${OUT_DIR}/00-summary.txt"
echo "  ${OUT_DIR}/01-docker-node-ls.txt"
echo "  ${OUT_DIR}/02-docker-stack-services-${STACK_NAME}.txt"
echo "  ${OUT_DIR}/03-docker-service-ps-*.txt"
echo "  ${OUT_DIR}/04-docker-service-logs-*.txt"
echo "  ${OUT_DIR}/10-curl-health.txt"
echo "  ${OUT_DIR}/11-curl-create-user.txt"
echo "  ${OUT_DIR}/12-curl-create-post.txt"
echo "  ${OUT_DIR}/13-curl-feed.txt"
