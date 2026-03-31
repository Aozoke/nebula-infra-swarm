#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-nebula}"

if [[ "$(docker info --format '{{.Swarm.ControlAvailable}}')" != "true" ]]; then
  echo "Error: run this script on a Swarm manager node."
  exit 1
fi

if ! docker secret inspect nebula_postgres_password >/dev/null 2>&1; then
  echo "Error: missing Docker secret 'nebula_postgres_password'."
  echo "Create it first, for example:"
  echo "  printf '<PASSWORD>' | docker secret create nebula_postgres_password -"
  exit 1
fi

docker stack deploy --detach=false \
  -c deploy/swarm/base/stack.data.yml \
  -c deploy/swarm/base/stack.edge.yml \
  -c deploy/swarm/base/stack.apps.yml \
  -c deploy/swarm/overlays/3vm-placement.yml \
  -c deploy/swarm/overlays/registry-images.yml \
  "${STACK_NAME}"

echo
echo "Deployed stack with registry images: ${STACK_NAME}"
docker stack services "${STACK_NAME}"
