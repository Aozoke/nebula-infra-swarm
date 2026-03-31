# Présentation Nebula (MVP + Cluster 3 VM) — Version détaillée

> Note: version compacte pour PPT/Gamma disponible ici:
> `docs/procedures/presentation-jury-12slides.md`

## Slide 1 — Titre
- **Nebula Infrastructure MVP (Docker Swarm)**
- Sujet: prouver l'infrastructure microservices, pas un produit complet.
- Auteur, date, environnement de démo.

## Slide 2 — Objectif du projet
- Démontrer une architecture opérable en Swarm.
- Valider: routage, inter-service, persistance, asynchrone, cache, update/rollback.
- Démarche: MVP sur VM1 puis passage en cluster réel 3 VM.

## Slide 3 — Contexte technique
- Manager Swarm: `10.100.9.222` (`ubuntu1-lefevret`).
- Worker app: `10.100.9.135` (`ubuntu2-lefevret`).
- Worker data: `10.100.9.223` (`ubuntu3-lefevret`).
- Stack technique: Docker Swarm, Traefik, Postgres, Redis Streams, FastAPI, Portainer, Registry privé, Prometheus, Grafana.

## Slide 4 — Topologie cible retenue
- VM1 = `manager-edge`
- VM2 = `worker-app`
- VM3 = `worker-data`
- Réseaux overlay: `public`, `app`, `data`
- Exposition publique: **edge-proxy seulement**

## Slide 5 — Déploiement final obtenu (3 VM)
- `edge-proxy` sur VM1 (manager-edge)
- `users-api`, `posts-api`, `feed-api`, `feed-worker` sur VM2 (worker-app)
- `postgres`, `redis` sur VM3 (worker-data)
- Validation faite avec `docker service ps` service par service.

## Slide 6 — Découpage des stacks
- `deploy/swarm/base/stack.data.yml` -> postgres + redis + réseaux/volumes/secrets
- `deploy/swarm/base/stack.edge.yml` -> Traefik
- `deploy/swarm/base/stack.apps.yml` -> microservices métiers
- `deploy/swarm/base/stack.admin.yml` -> Portainer
- `deploy/swarm/base/stack.registry.yml` -> registry Docker privé
- `deploy/swarm/base/stack.monitoring.yml` -> node-exporter + Prometheus + Grafana
- `deploy/swarm/overlays/3vm-placement.yml` -> contraintes de placement par labels
- `deploy/swarm/overlays/registry-images.yml` -> bascule images vers le registry privé

## Slide 6 bis — Pourquoi ces dossiers/fichiers existent
- `services/`:
  - contient le code minimal métier de chaque microservice (`users-api`, `posts-api`, `feed-api`, `feed-worker`)
  - chaque service a son `Dockerfile` + `requirements.txt` + `app/main.py` pour être buildable indépendamment
- `deploy/swarm/base/`:
  - contient les stacks Swarm stables par domaine (edge, data, apps, admin, registry, monitoring)
  - objectif: limiter l’impact d’un changement (on modifie une brique sans casser les autres)
- `deploy/swarm/overlays/`:
  - contient les variations d’environnement (placement 3 VM, images registry)
  - objectif: changer le comportement de déploiement sans dupliquer toute la stack
- `scripts/deploy/`:
  - automatise labels + déploiements pour réduire les erreurs manuelles
- `scripts/test/`:
  - automatise smoke tests et collecte des preuves soutenance
- `docs/procedures/`:
  - centralise le support oral (présentation), l’explication code et le runbook des manipulations

## Slide 7 — Labels et placement
- Labels nœuds:
  - VM1: `role=edge`
  - VM2: `role=app`
  - VM3: `role=data`
- Contraintes utilisées dans l'overlay:
  - edge-proxy -> manager + `role=edge`
  - apps -> `role=app`
  - data services -> `role=data`

## Slide 8 — Services et endpoints (vue rapide)
- `users-api`: `/health`, `/users`, `/follows`, `/internal/...`
- `posts-api`: `/posts`
- `feed-api`: `/feed/{user_id}`
- `feed-worker`: interne, pas exposé publiquement

## Slide 9 — Flux applicatif démontré
1. `POST /posts` arrive sur `posts-api`
2. `posts-api` vérifie l'auteur via `users-api`
3. `posts-api` écrit en Postgres
4. `posts-api` publie `post.created` dans Redis Stream `nebula.events`
5. `feed-worker` consomme et écrit `feed_events`
6. `feed-api` lit le feed (Redis cache puis Postgres)

## Slide 10 — Persistance et asynchrone
- Persistance:
  - Postgres volumes (`postgres_data`)
  - Redis AOF (`redis_data`, `--appendonly yes`)
- Asynchrone:
  - Redis Streams (pas Pub/Sub) pour rejouabilité et robustesse

## Slide 11 — Sécurité minimale appliquée
- Mot de passe DB hors dépôt via `docker secret` (`nebula_postgres_password`)
- `postgres` et `redis` uniquement réseau interne `data`
- Point d'entrée unique: Traefik (`public`)
- Services internes non exposés en ports host

## Slide 12 — Versionning et exploitation
- Images taggées:
  - `nebula/users-api:v0.3.0`
  - `nebula/posts-api:v0.2.0`
  - `nebula/feed-api:v0.3.0`
  - `nebula/feed-worker:v0.1.0`
- `update_config` + `rollback_config` sur services stateless

## Slide 13 — Incident réel: MTU / VXLAN
- Symptôme: `docker swarm join` timeout/pending malgré connectivité de base.
- Cause lab: MTU trop haute pour encapsulation VXLAN.
- Vérification:
```bash
ping -M do -s 1450 10.100.9.222
ping -M do -s 1372 10.100.9.222
```
- Correctif:
  - `/etc/netplan/50-cloud-init.yaml` -> `mtu: 1400` sur `eth0`
  - `sudo netplan apply`

## Slide 14 — Démo live (séquence)
1. Vérifier santé globale (`/health`)
2. Créer un user
3. Créer un post avec cet user
4. Lire le feed de cet user
5. Montrer logs worker/feed-api

## Slide 15 — Commandes démo
```bash
curl -i http://127.0.0.1/health

curl -i -X POST http://127.0.0.1/users \
  -H 'Content-Type: application/json' \
  -d '{"handle":"demo3vm"}'

curl -i -X POST http://127.0.0.1/posts \
  -H 'Content-Type: application/json' \
  -d '{"author_id":"user-1","content":"test 3vm"}'

curl -i http://127.0.0.1/feed/user-1
```

## Slide 16 — Vérification exploitation
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

## Slide 17 — Interface visuelle (Portainer)
- Déployé dans stack dédiée `portainer`.
- Accès via tunnel SSH:
```bash
ssh -N -J root@10.210.0.9 -L 9444:127.0.0.1:9443 etudiant@10.100.9.222
```
- Ouvrir `https://127.0.0.1:9444`.

## Slide 18 — Geler les preuves (soutenance)
- Script ajouté:
```bash
cd /home/etudiant/Nebula-infra-swarm
./scripts/test/freeze-evidence-3vm.sh
```
- Sortie:
  - `docs/evidence/<timestamp>/` avec `node ls`, `stack services`, `service ps`, logs, réponses curl.

## Slide 19 — Ce qui est validé
- Cluster Swarm 3 nœuds opérationnel.
- Placement conforme à l'architecture (edge/app/data).
- Flux end-to-end validé (`users -> posts -> stream -> worker -> feed`).
- Cache Redis feed observé (`cache miss` puis `cache hit`).
- Registry privé opérationnel (`10.100.9.222:5000`) + images poussées.
- Monitoring opérationnel (`monitoring_node-exporter` global `3/3`, Prometheus `1/1`, Grafana `1/1`).

## Slide 20 — Ce qui reste à faire (projet)
- Dashboards Grafana métier/infrastructure plus complets + alertes utiles.
- Pipeline CI/CD build/tag/push (éviter les pushes manuels).
- Tests de charge et mesures (RPS, latences, taux erreur, cache hit ratio)
- Démo rollback explicite d'une version applicative
- Documentation runbook incident/reprise plus détaillée

## Slide 21 — Préparation Terraform (prochaine itération)
- Cible: environnement recréable de A à Z.
- Flux:
  1. Terraform provisionne VMs + réseau
  2. bootstrap Docker + Swarm
  3. récupération repo
  4. lancement script one-shot
- Intégration future au même support de présentation.

## Slide 22 — Conclusion
- Objectif infra atteint: plateforme Nebula MVP opérable en Swarm.
- Résultat clé: passage réussi de 1 VM à 3 VM avec contraintes de placement.
- Valeur démontrée: exploitation, isolation réseau, persistance, asynchrone, cache, registry, monitoring.
- Prochaine marche: industrialisation CI/CD + tests de charge + Terraform.

---

## Notes speaker (oral)
- Le code métier est volontairement minimal: il sert à prouver le comportement infra.
- Montrer les logs comme preuve (inter-service + streams + cache).
- Distinguer clairement:
  - **fait et démontré**
  - **prêt pour prochaine itération**
