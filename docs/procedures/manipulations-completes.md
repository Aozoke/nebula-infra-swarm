# Manipulations complètes (ordre réel du projet)

Ce runbook rassemble les commandes clés à rejouer/expliquer en soutenance.

## A) Base cluster Swarm (VM1 manager + VM2/VM3 workers)

### VM1
```bash
docker swarm init --advertise-addr 10.100.9.222
docker swarm join-token worker
docker node ls
```

### VM2 / VM3
```bash
sudo docker swarm join --token <TOKEN_WORKER> 10.100.9.222:2377
```

### VM1 (labels)
```bash
docker node update --label-add role=edge ubuntu1-lefevret
docker node update --label-add role=app ubuntu2-lefevret
docker node update --label-add role=data ubuntu3-lefevret
docker node ls
```

## B) Correctif réseau MTU (incident VXLAN)

Sur les VM concernées:
```bash
sudo nano /etc/netplan/50-cloud-init.yaml
# ajouter sous eth0:
# mtu: 1400
sudo netplan apply
ip link show eth0 | grep mtu
```

Test:
```bash
ping -M do -s 1450 10.100.9.222
ping -M do -s 1372 10.100.9.222
```

## C) Secret DB + déploiement Nebula 3 VM

### VM1
```bash
printf '<PASSWORD>' | docker secret create nebula_postgres_password -
```

Déploiement:
```bash
cd /home/etudiant/Nebula-infra-swarm
docker stack deploy --detach=false \
  -c deploy/swarm/base/stack.data.yml \
  -c deploy/swarm/base/stack.edge.yml \
  -c deploy/swarm/base/stack.apps.yml \
  -c deploy/swarm/overlays/3vm-placement.yml \
  nebula
```

Vérification:
```bash
docker stack services nebula
docker stack ps nebula
```

## D) Validation fonctionnelle (write -> stream -> worker -> feed)

```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"demo"}'
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"test"}'
curl -i http://127.0.0.1/feed/user-1
docker service logs --tail 30 nebula_posts-api
docker service logs --tail 30 nebula_feed-worker
docker service logs --tail 30 nebula_feed-api
```

## D bis) Test de résilience par suppression (étape soutenance)

Objectif:
- supprimer un conteneur d’un service Swarm managé, puis vérifier la recréation automatique.

Exemple avec `edge-proxy` (sur VM1):
```bash
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=nebula_edge-proxy | head -n 1)
docker rm -f "$CID"
sleep 3
docker service ps nebula_edge-proxy
```

Attendu:
- une tâche est arrêtée, puis une nouvelle tâche passe en `Running`.

## E) Portainer (admin)

### VM1
```bash
docker stack deploy --detach=false -c deploy/swarm/base/stack.admin.yml portainer
docker stack services portainer
```

Accès tunnel:
```bash
ssh -N -J root@10.210.0.9 -L 9444:127.0.0.1:9443 etudiant@10.100.9.222
```
URL:
- `https://127.0.0.1:9444`

## F) Registry privé + bascule images

### VM1 (registry)
```bash
scripts/deploy/deploy-registry.sh
docker stack services registry
curl -s http://127.0.0.1:5000/v2/_catalog
```

### VM1/VM2/VM3 (insecure registry)
```bash
sudo mkdir -p /etc/docker
echo '{"insecure-registries":["10.100.9.222:5000"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
sudo docker info | sed -n '/Insecure Registries:/,/Live Restore Enabled:/p'
```

### VM1 (tag/push)
```bash
docker tag nebula/users-api:v0.3.0 10.100.9.222:5000/nebula/users-api:v0.3.0
docker tag nebula/posts-api:v0.2.0 10.100.9.222:5000/nebula/posts-api:v0.2.0
docker tag nebula/feed-api:v0.3.0 10.100.9.222:5000/nebula/feed-api:v0.3.0
docker tag nebula/feed-worker:v0.1.0 10.100.9.222:5000/nebula/feed-worker:v0.1.0

docker push 10.100.9.222:5000/nebula/users-api:v0.3.0
docker push 10.100.9.222:5000/nebula/posts-api:v0.2.0
docker push 10.100.9.222:5000/nebula/feed-api:v0.3.0
docker push 10.100.9.222:5000/nebula/feed-worker:v0.1.0
```

### VM1 (mise à jour services avec images registry)
```bash
docker service update --detach=false --image 10.100.9.222:5000/nebula/users-api:v0.3.0 nebula_users-api
docker service update --detach=false --image 10.100.9.222:5000/nebula/posts-api:v0.2.0 nebula_posts-api
docker service update --detach=false --image 10.100.9.222:5000/nebula/feed-api:v0.3.0 nebula_feed-api
docker service update --detach=false --image 10.100.9.222:5000/nebula/feed-worker:v0.1.0 nebula_feed-worker
docker stack services nebula
```

## G) Monitoring (Prometheus + Grafana + node-exporter)

### VM1
```bash
printf '<STRONG_PASSWORD>' | docker secret create grafana_admin_password -
scripts/deploy/deploy-monitoring.sh
docker stack services monitoring
```

Validation:
```bash
curl -i http://127.0.0.1/grafana/login
docker service logs --tail 80 monitoring_prometheus
docker service logs --tail 80 monitoring_grafana
```

## H) Preuves soutenance

```bash
cd /home/etudiant/Nebula-infra-swarm
./scripts/test/freeze-evidence-3vm.sh
```

Sortie:
- `docs/evidence/<timestamp>/`
