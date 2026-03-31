# Nebula Infra Swarm

Infrastructure MVP de Nebula sur Docker Swarm, validée en cluster 3 nœuds.

## Topologie validée

- `ubuntu1-lefevret` (`10.100.9.222`) -> manager-edge
- `ubuntu2-lefevret` (`10.100.9.135`) -> worker-app
- `ubuntu3-lefevret` (`10.100.9.223`) -> worker-data

## Stacks

- `deploy/swarm/base/stack.data.yml` -> Postgres + Redis
- `deploy/swarm/base/stack.edge.yml` -> Traefik
- `deploy/swarm/base/stack.apps.yml` -> APIs + worker
- `deploy/swarm/base/stack.admin.yml` -> Portainer
- `deploy/swarm/base/stack.registry.yml` -> Docker Registry privé
- `deploy/swarm/base/stack.monitoring.yml` -> Prometheus + Grafana + node-exporter
- `deploy/swarm/overlays/3vm-placement.yml` -> contraintes de placement

## Déploiement principal (3 VM)

```bash
cd /home/etudiant/Nebula-infra-swarm
scripts/deploy/one-button-3vm.sh ubuntu1-lefevret ubuntu2-lefevret ubuntu3-lefevret
```

Déploiement complet (Nebula + Portainer + Registry + Monitoring):

```bash
printf '<STRONG_PASSWORD>' | docker secret create grafana_admin_password -
cd /home/etudiant/Nebula-infra-swarm
scripts/deploy/one-button-full.sh ubuntu1-lefevret ubuntu2-lefevret ubuntu3-lefevret
```

## Déploiements additionnels

Registry:

```bash
cd /home/etudiant/Nebula-infra-swarm
scripts/deploy/deploy-registry.sh
```

Nebula avec images registry:

```bash
cd /home/etudiant/Nebula-infra-swarm
scripts/deploy/deploy-nebula-3vm-registry.sh
```

Monitoring:

```bash
printf '<STRONG_PASSWORD>' | docker secret create grafana_admin_password -
cd /home/etudiant/Nebula-infra-swarm
scripts/deploy/deploy-monitoring.sh
```

Note: le monitoring utilise le réseau externe `nebula_app` (stack `nebula` déjà déployée).

## Preuves soutenance

```bash
cd /home/etudiant/Nebula-infra-swarm
scripts/test/freeze-evidence-3vm.sh
```

Les preuves sont déposées dans `docs/evidence/<timestamp>/`.

## Documentation

- Architecture: `docs/architecture/cluster-topology.md`
- Runbook complet commandes: `docs/procedures/manipulations-completes.md`
- Présentation complète projet: `docs/procedures/presentation-vm1-nebula.md`
- Explication code: `docs/procedures/code-walkthrough-main-py.md`
