#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <EDGE_NODE> <APP_NODE> <DATA_NODE>"
  echo "Example: $0 ubuntu1-lefevret ubuntu2-lefevret ubuntu3-lefevret"
  exit 1
fi

EDGE_NODE="$1"
APP_NODE="$2"
DATA_NODE="$3"

if ! docker secret inspect grafana_admin_password >/dev/null 2>&1; then
  echo "Error: missing Docker secret 'grafana_admin_password'."
  echo "Create it first:"
  echo "  printf '<STRONG_PASSWORD>' | docker secret create grafana_admin_password -"
  exit 1
fi

echo "[1/6] Label nodes"
scripts/deploy/label-nodes-3vm.sh "${EDGE_NODE}" "${APP_NODE}" "${DATA_NODE}"

echo
echo "[2/6] Deploy Nebula (3 VM placement)"
scripts/deploy/deploy-nebula-3vm.sh

echo
echo "[3/6] Deploy Portainer"
docker stack deploy --detach=false -c deploy/swarm/base/stack.admin.yml portainer

echo
echo "[4/6] Deploy Registry"
scripts/deploy/deploy-registry.sh

echo
echo "[5/6] Deploy Monitoring"
scripts/deploy/deploy-monitoring.sh

echo
echo "[6/6] Run Nebula smoke retest"
scripts/test/retest-3vm.sh
