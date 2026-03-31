#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-registry}"

if [[ "$(docker info --format '{{.Swarm.ControlAvailable}}')" != "true" ]]; then
  echo "Error: run this script on a Swarm manager node."
  exit 1
fi

docker stack deploy --detach=false \
  -c deploy/swarm/base/stack.registry.yml \
  "${STACK_NAME}"

echo
echo "Deployed stack: ${STACK_NAME}"
docker stack services "${STACK_NAME}"
