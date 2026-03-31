# Explication du code + manipulations (version oral)

Ce document est fait pour expliquer rapidement:
- ce que fait chaque `main.py`
- comment les services coopèrent
- quelles commandes prouver en live

## 1) `services/users-api/app/main.py`

### Rôle
- Service de référence pour identités et relations (`users`, `follows`).

### Points techniques à dire
- Lit le secret DB via `DATABASE_PASSWORD_FILE`.
- Initialise le schéma au démarrage (`users`, `follows`).
- Endpoints publics:
  - `GET /health`
  - `POST /users`
  - `GET /users/{user_id}`
  - `POST /follows`
  - `DELETE /follows`
- Endpoints internes:
  - `GET /internal/users/{user_id}/exists`
  - `GET /internal/users/{user_id}/followers`

### Preuve rapide
```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"demo-user"}'
```

## 2) `services/posts-api/app/main.py`

### Rôle
- Gère l'écriture de posts et publie l'événement asynchrone.

### Points techniques à dire
- Vérifie l’auteur via `users-api` (`/internal/users/{id}/exists`).
- Insère le post en Postgres.
- Publie `post.created` dans Redis Streams (`nebula.events`).

### Preuve rapide
```bash
curl -i -X POST http://127.0.0.1/posts \
  -H 'Content-Type: application/json' \
  -d '{"author_id":"user-1","content":"demo post"}'
docker service logs --tail 30 nebula_posts-api
```

## 3) `services/feed-worker/app/main.py`

### Rôle
- Worker interne (pas exposé) qui consomme le stream et construit la projection feed.

### Points techniques à dire
- Lit Redis Streams en continu.
- Filtre l'événement `post.created`.
- Écrit dans la table `feed_events` (Postgres).

### Preuve rapide
```bash
docker service logs --tail 50 nebula_feed-worker
```
Attendu:
- `event received post.created ...`
- `feed event stored ...`

## 4) `services/feed-api/app/main.py`

### Rôle
- Service de lecture du feed.

### Points techniques à dire
- Endpoint: `GET /feed/{user_id}`.
- Cache Redis (`feed:user:{id}`) avec TTL.
- Fallback Postgres en cache miss.

### Preuve rapide
```bash
curl -i http://127.0.0.1/feed/user-1
curl -i http://127.0.0.1/feed/user-1
docker service logs --tail 50 nebula_feed-api
```
Attendu:
- 1er appel: `cache miss`
- 2e appel: `cache hit`

## 5) Ce que prouve l'architecture
- Communication inter-services (`posts-api -> users-api`).
- Persistance (`postgres`, `redis AOF`).
- Asynchrone découplé (`posts-api -> stream -> worker`).
- Exploitabilité (stack, logs, placement, update/rollback).

## 6) Manipulation complète (ordre soutenance)

## 6.1 Vérifier cluster et placement
```bash
docker node ls
docker stack services nebula
docker service ps nebula_edge-proxy
docker service ps nebula_users-api
docker service ps nebula_posts-api
docker service ps nebula_feed-api
docker service ps nebula_feed-worker
docker service ps nebula_postgres
docker service ps nebula_redis
```

## 6.2 Démo fonctionnelle
```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"demo-final"}'
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"test final"}'
curl -i http://127.0.0.1/feed/user-1
```

## 6.3 Registry privé (déjà validé)
```bash
docker stack services registry
curl -s http://127.0.0.1:5000/v2/_catalog
```

## 6.4 Monitoring (déjà validé)
```bash
docker stack services monitoring
curl -i http://127.0.0.1/grafana/login
docker service logs --tail 50 monitoring_prometheus
docker service logs --tail 50 monitoring_grafana
```

## 6.5 Geler les preuves
```bash
cd /home/etudiant/Nebula-infra-swarm
./scripts/test/freeze-evidence-3vm.sh
```
Sortie:
- `docs/evidence/<timestamp>/`

## 7) Message final oral (30 secondes)
- "Le code applicatif est volontairement minimal."
- "La valeur démontrée est infra: réseau, isolation, persistance, asynchrone, observabilité."
- "Le passage 1 VM -> 3 VM est prouvé avec placement par rôle."
- "Registry privé et monitoring sont opérationnels; la suite est CI/CD, perf, rollback et Terraform."
