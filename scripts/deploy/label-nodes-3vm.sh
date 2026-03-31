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

if [[ "${EDGE_NODE}" == "${APP_NODE}" || "${EDGE_NODE}" == "${DATA_NODE}" || "${APP_NODE}" == "${DATA_NODE}" ]]; then
  echo "Error: EDGE_NODE, APP_NODE and DATA_NODE must be 3 different nodes."
  exit 1
fi

if [[ "$(docker info --format '{{.Swarm.ControlAvailable}}')" != "true" ]]; then
  echo "Error: run this script on a Swarm manager node."
  exit 1
fi

for node in "${EDGE_NODE}" "${APP_NODE}" "${DATA_NODE}"; do
  docker node inspect "${node}" >/dev/null
done

# Clear previous role labels to avoid ambiguous placement.
while IFS= read -r node_id; do
  docker node update --label-rm role "${node_id}" >/dev/null || true
done < <(docker node ls -q)

docker node update --label-add role=edge "${EDGE_NODE}" >/dev/null
docker node update --label-add role=app "${APP_NODE}" >/dev/null
docker node update --label-add role=data "${DATA_NODE}" >/dev/null

echo "Node labels updated:"
while IFS= read -r node_id; do
  docker node inspect --format '{{.Description.Hostname}} role={{index .Spec.Labels "role"}}' "${node_id}"
done < <(docker node ls -q)
