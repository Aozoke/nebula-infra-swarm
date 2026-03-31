# Nebula — Support jury 12 slides (version opérationnelle)

Utilisation: ce fichier est prêt à être collé dans Gamma/PPT.  
Format conseillé: 1 idée par slide + 1 preuve terminal.

## Slide 1 — Titre et objectif

- **Nebula Infrastructure MVP sur Docker Swarm**
- Objectif: prouver une plateforme microservices opérable, pas un produit final.
- Résultat attendu: déploiement distribué, flux end-to-end, preuves techniques.

Action live:
- Pas de commande (slide d'ouverture).

Preuve:
- Contexte projet et périmètre explicités.

## Slide 2 — Topologie validée (3 VM)

- VM1 `10.100.9.222`: manager + edge.
- VM2 `10.100.9.135`: worker app.
- VM3 `10.100.9.223`: worker data.
- Isolation logique par rôles.

Action live:
```bash
docker node ls
```

Preuve:
- 1 manager + 2 workers en `Ready/Active`.

## Slide 3 — Architecture de stack

- `edge-proxy` (Traefik), `users-api`, `posts-api`, `feed-api`, `feed-worker`, `postgres`, `redis`.
- Réseaux overlay: `public`, `app`, `data`.
- Point d'entrée unique via Traefik.

Action live:
```bash
docker stack services nebula
```

Preuve:
- Tous les services sont visibles et répliqués.

## Slide 4 — Déploiement et orchestration

- Déploiement depuis VM1 manager avec fichiers stack + overlay placement.
- Stratégie de mise à jour contrôlée (`start-first`, rollback config).
- Déploiement reproductible.

Action live:
```bash
docker stack ps nebula
```

Preuve:
- Tâches services en `Running`, historique des redémarrages visible.

## Slide 5 — Labels et placement des services

- Labels nœuds: `role=edge`, `role=app`, `role=data`.
- Placement cible: `edge-proxy` sur edge.
- Placement cible: APIs + worker sur app.
- Placement cible: Postgres + Redis sur data.

Action live:
```bash
docker node inspect ubuntu1-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu2-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu3-lefevret --format '{{ .Spec.Labels }}'
docker service ps nebula_postgres
docker service ps nebula_redis
```

Preuve:
- Labels corrects + data services réellement exécutés sur VM3.

## Slide 6 — APIs exposées et routage Traefik

- `users-api`: `/health`, `/users`, `/follows`.
- `posts-api`: `/posts`.
- `feed-api`: `/feed/{user_id}`.
- Routage HTTP centralisé par Traefik.

Action live:
```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"jury-demo"}'
```

Preuve:
- Réponses HTTP `200` et `201`.

## Slide 7 — Flux asynchrone (post -> stream -> feed)

- `posts-api` vérifie l'auteur via `users-api`.
- `posts-api` écrit en DB puis publie `post.created` dans Redis Streams.
- `feed-worker` consomme l'événement et alimente `feed_events`.

Action live:
```bash
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"post jury"}'
docker service logs --tail 40 nebula_feed-worker
```

Preuve:
- Event reçu/corrélé dans les logs du worker.

## Slide 8 — Lecture feed + cache Redis

- `feed-api` expose `GET /feed/{user_id}`.
- Premier appel: DB + cache write (miss).
- Appels suivants: cache hit.

Action live:
```bash
curl -i http://127.0.0.1/feed/user-1
curl -i http://127.0.0.1/feed/user-1
docker service logs --tail 40 nebula_feed-api
```

Preuve:
- Logs `cache miss` puis `cache hit`.

## Slide 9 — Persistance et sécurité minimale

- Postgres persistant via volume.
- Redis persistant via AOF.
- Secret DB injecté via Docker secret.
- Pas d'exposition directe de Postgres/Redis sur l'hôte.

Action live:
```bash
docker secret ls
docker volume ls | grep -E 'postgres|redis'
docker service ps nebula_postgres
docker service ps nebula_redis
```

Preuve:
- Secret présent + volumes présents + services data en running.

## Slide 10 — Exploitation: Portainer et Registry privé

- Portainer pour supervision visuelle.
- Registry privé pour partager les images dans le cluster.
- Réduction de la dépendance aux images locales.

Action live:
```bash
docker stack services portainer
docker stack services registry
curl -s http://127.0.0.1:5000/v2/_catalog
```

Preuve:
- Stacks admin/registry actives + catalog JSON du registry.

## Slide 11 — Incident réel et résolution (MTU VXLAN)

- Problème rencontré: `swarm join` en timeout.
- Diagnostic: contrainte MTU sur encapsulation VXLAN.
- Correctif: `mtu: 1400` appliqué sur `eth0`.

Action live:
```bash
ip link show eth0 | grep mtu
ping -M do -s 1450 10.100.9.222 || true
ping -M do -s 1372 10.100.9.222
```

Preuve:
- MTU visible à 1400 + test PMTU cohérent.

## Slide 12 — Limites, réplication et suite

- Aujourd'hui: réplication Swarm côté apps possible (`replicas`).
- Limite actuelle: data layer en instance unique (pas de réplication Postgres/Redis multi-noeuds).
- Prochaine itération: HA data (patroni/sentinel ou équivalent), CI/CD, Terraform provisioning complet.

Action live:
```bash
docker service scale nebula_users-api=2 nebula_posts-api=2 nebula_feed-api=2
docker stack services nebula
```

Preuve:
- `replicas` applicatives qui montent à `2/2`.
- Message oral clair: HA applicative OK, HA base de données à faire ensuite.
