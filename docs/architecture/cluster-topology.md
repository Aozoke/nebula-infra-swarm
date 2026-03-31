# Nebula Cluster Topology (Swarm)

## Objectif

Document de référence pour éviter les erreurs de rôle/IP pendant l'extension du cluster.

## Topologie cible (3 VM)

| VM | Hostname (exemple) | IP | Rôle Swarm | Rôle Nebula |
|---|---|---|---|---|
| VM1 | `ubuntu1-lefevret` | `10.100.9.222` | manager (leader) | edge / entrypoint |
| VM2 | `ubuntu2-lefevret` | `10.100.9.135` | worker | app (users-api, posts-api, feed-api, feed-worker) |
| VM3 | `ubuntu3-...` | `10.100.9.223` | worker | data (postgres, redis) |

> Note: ce mapping est celui validé dans votre lab (`.135 / .222 / .223`).
> Si les IP changent dans un autre environnement, garde la logique de rôles et mets ce tableau à jour.

## Commandes Swarm de base

### Sur VM1 (manager)

```bash
docker swarm init --advertise-addr 10.100.9.222
docker swarm join-token worker
docker node ls
```

### Sur VM2 et VM3 (workers)

```bash
docker swarm join --token <TOKEN_WORKER> 10.100.9.222:2377
```

## Labels recommandés (après join)

### Sur VM1 (manager)

```bash
docker node update --label-add role=edge <NODE_VM1>
```

### Sur VM2

```bash
docker node update --label-add role=app <NODE_VM2>
```

### Sur VM3

```bash
docker node update --label-add role=data <NODE_VM3>
```

## Placement cible des services

- `edge-proxy` -> noeud label `role=edge`
- `users-api`, `posts-api`, `feed-api`, `feed-worker` -> noeud label `role=app`
- `postgres`, `redis` -> noeud label `role=data`

## Vérifications rapides

```bash
docker node ls
docker stack services nebula
docker stack ps nebula
```
