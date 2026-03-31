# Nebula — Support jury 10 slides (version opérationnelle)

Utilisation: ce fichier est prêt à être collé dans Gamma/PPT.  
Format conseillé: 1 idée forte par slide.

## Slide 1 — Problème et objectif

- **Nebula Infrastructure MVP sur Docker Swarm**
- Enjeu: démontrer une plateforme microservices exploitable en conditions lab.
- Cible de démonstration: déploiement distribué + preuve technique bout-en-bout.

## Slide 2 — Topologie 3 VM et rôles

- VM1 `10.100.9.222`: manager + edge.
- VM2 `10.100.9.135`: worker applicatif.
- VM3 `10.100.9.223`: worker data.
- Séparation des rôles pour limiter les couplages runtime.

## Slide 3 — Architecture des services

- Services: Traefik, users-api, posts-api, feed-api, feed-worker, Postgres, Redis.
- Réseaux overlay: `public` (entrée), `app` (métier), `data` (persistance).
- Point d'entrée unique: Traefik, pas d'exposition directe des services data.

## Slide 4 — Déploiement Swarm reproductible

- Déploiement via stacks découpées (`data`, `edge`, `apps`) + overlay de placement.
- Configuration update/rollback sur les services stateless.
- Résultat: un déploiement cohérent et rejouable.

## Slide 5 — Placement contrôlé par labels

- Labels nœuds: `role=edge`, `role=app`, `role=data`.
- Placement cible:
- `edge-proxy` sur edge.
- APIs + worker sur app.
- Postgres + Redis sur data.

## Slide 6 — Parcours fonctionnel API (synchrone)

- `users-api`: santé + gestion utilisateurs/relations.
- `posts-api`: création post avec contrôle auteur.
- `feed-api`: lecture feed utilisateur.
- Démonstration via appels HTTP depuis VM1.

## Slide 7 — Asynchrone et cache (valeur technique)

- `posts-api` publie `post.created` dans Redis Streams.
- `feed-worker` consomme les événements et alimente la projection.
- `feed-api` applique cache Redis (miss puis hit) pour accélérer la lecture.

## Slide 8 — Persistance, secrets, exploitation

- Persistance: volume Postgres + AOF Redis.
- Secret DB via Docker secrets (hors code).
- Exploitation: Portainer (visuel) + registry privé (diffusion d’images intra-cluster).

## Slide 9 — Incident réel et résolution

- Incident observé: échec `swarm join` (timeout/pending).
- Diagnostic: contrainte MTU avec VXLAN.
- Résolution: `mtu: 1400` sur `eth0`, puis rejoin validé.
- Valeur: preuve de troubleshooting infra réel.

## Slide 10 — Résultats, limites, suite

- Résultats: cluster 3 nœuds opérationnel, flux E2E validé, placement conforme.
- Réplication actuelle: scalable côté apps (`replicas`), couche data en instance unique.
- Suite: HA data, CI/CD, Terraform pour provisioning/redeployment complet.

---

## Annexe — Actions live et preuves (par slide)

### Slide 1

Action live:
- Pas de commande (slide d’ouverture).

Preuve:
- Objectif et périmètre clairement cadrés.

### Slide 2

Action live:
```bash
docker node ls
```

Preuve:
- 1 manager + 2 workers en `Ready/Active`.

### Slide 3

Action live:
```bash
docker stack services nebula
```

Preuve:
- Tous les services attendus sont présents.

### Slide 4

Action live:
```bash
docker stack ps nebula
```

Preuve:
- Tâches en `Running` et historique observable.

### Slide 5

Action live:
```bash
docker node inspect ubuntu1-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu2-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu3-lefevret --format '{{ .Spec.Labels }}'
docker service ps nebula_postgres
docker service ps nebula_redis
```

Preuve:
- Labels corrects + services data exécutés sur VM3.

### Slide 6

Action live:
```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"jury-demo"}'
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"post jury"}'
```

Preuve:
- Réponses HTTP attendues (`200/201`) sur le parcours synchrone.

### Slide 7

Action live:
```bash
curl -i http://127.0.0.1/feed/user-1
curl -i http://127.0.0.1/feed/user-1
docker service logs --tail 40 nebula_feed-worker
docker service logs --tail 40 nebula_feed-api
```

Preuve:
- Événement consommé + cache miss/hit visibles.

### Slide 8

Action live:
```bash
docker secret ls
docker volume ls | grep -E 'postgres|redis'
docker stack services portainer
docker stack services registry
curl -s http://127.0.0.1:5000/v2/_catalog
```

Preuve:
- Secret/volumes présents + outillage d’exploitation actif.

### Slide 9

Action live:
```bash
ip link show eth0 | grep mtu
ping -M do -s 1450 10.100.9.222 || true
ping -M do -s 1372 10.100.9.222
```

Preuve:
- MTU appliquée et comportement PMTU cohérent.

### Slide 10

Action live:
```bash
docker service scale nebula_users-api=2 nebula_posts-api=2 nebula_feed-api=2
docker stack services nebula
```

Preuve:
- Réplicas applicatifs montent à `2/2`.
- Message de clôture: HA applicative validée, HA data à implémenter ensuite.
