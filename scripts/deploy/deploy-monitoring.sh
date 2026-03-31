#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-monitoring}"

if [[ "$(docker info --format '{{.Swarm.ControlAvailable}}')" != "true" ]]; then
  echo "Error: run this script on a Swarm manager node."
  exit 1
fi

if ! docker secret inspect grafana_admin_password >/dev/null 2>&1; then
  echo "Error: missing Docker secret 'grafana_admin_password'."
  echo "Create it first, for example:"
  echo "  printf '<STRONG_PASSWORD>' | docker secret create grafana_admin_password -"
  exit 1
fi

docker stack deploy --detach=false \
  -c deploy/swarm/base/stack.monitoring.yml \
  "${STACK_NAME}"

echo
echo "Deployed stack: ${STACK_NAME}"
docker stack services "${STACK_NAME}"
