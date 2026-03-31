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

echo "[1/4] Label nodes"
scripts/deploy/label-nodes-3vm.sh "${EDGE_NODE}" "${APP_NODE}" "${DATA_NODE}"

echo
echo "[2/4] Deploy Nebula (3 VM placement overlay)"
scripts/deploy/deploy-nebula-3vm.sh

echo
echo "[3/4] Deploy Portainer admin stack"
docker stack deploy --detach=false -c deploy/swarm/base/stack.admin.yml portainer

echo
echo "[4/4] Run smoke retest"
scripts/test/retest-3vm.sh
