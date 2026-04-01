# Nebula — Support jury 10 slides (Partie 1: Docker Swarm)

Utilisation: ce fichier est prêt à être collé dans Gamma/PPT.  
Format conseillé: 1 idée forte par slide.

## Slide 1 — Plan de soutenance (partie Swarm)

- Cette première partie est dédiée à Docker Swarm uniquement.
- Étape 1: présenter l'architecture, ce qui a été réalisé, les secrets, les services et la résilience.
- Étape 2: supprimer un service/processus pour tester la résilience.
- Étape 3: analyser le code de déploiement Docker Swarm.

## Slide 2 — Docker Swarm et topologie cluster

- Cluster 3 VM:
- VM1 `10.100.9.222` = manager + edge.
- VM2 `10.100.9.135` = worker app.
- VM3 `10.100.9.223` = worker data.
- Objectif: séparer entrée, logique applicative et data.

## Slide 3 — Ce que j’ai réalisé (de 1 VM vers 3 VM)

- D’abord un MVP fonctionnel sur 1 VM pour valider le socle.
- Ensuite extension vers 3 VM avec placement par rôles.
- Industrialisation avec un "bouton" de déploiement:
- `scripts/deploy/one-button-3vm.sh` (labels + déploiement + smoke test).

## Slide 4 — Gestion des secrets

- Secret DB géré via Docker secrets (`nebula_postgres_password`).
- Mot de passe non stocké en dur dans le code.
- Les services lisent le secret via `*_PASSWORD_FILE`.

## Slide 5 — Services déployés et placement

- Services déployés: `edge-proxy`, `users-api`, `posts-api`, `feed-api`, `feed-worker`, `postgres`, `redis`.
- Placement par labels:
- `edge-proxy` sur edge.
- APIs + worker sur app.
- `postgres` + `redis` sur data.

## Slide 6 — Résilience native Swarm

- Redémarrage automatique des tâches en échec.
- Réconciliation d’état (Swarm maintient le nombre de replicas demandé).
- Politique de mise à jour contrôlée pour services stateless.

## Slide 7 — Test de résilience par suppression

- Test: suppression forcée d’un conteneur de service.
- Résultat attendu: Swarm recrée automatiquement une nouvelle tâche.
- Ce test prouve que le service reste géré par l’orchestrateur, pas par un conteneur unique.

## Slide 8 — Analyse du code Docker Swarm

- Lecture des fichiers de stack (`stack.data.yml`, `stack.edge.yml`, `stack.apps.yml`).
- Lecture des overlays (`3vm-placement.yml`) pour comprendre les contraintes.
- Lecture des scripts (`one-button-3vm.sh`, `deploy-nebula-3vm.sh`) pour expliquer l'automatisation.

## Slide 9 — Bilan technique de la partie Swarm

- Ce qui est validé:
- cluster 3 nœuds opérationnel.
- services déployés et placés correctement.
- secrets gérés.
- test de résilience validé.
- analyse du code de déploiement réalisée.

## Slide 10 — Transition vers la partie 2 (Terraform)

- Cette partie 1 valide l’exploitation sur cluster existant.
- Partie 2 (autre PPT): créer 3 nouvelles VM via Terraform.
- Puis récupérer le code depuis Git et redéployer Nebula sur ce nouvel environnement.

---

## Annexe — Actions live et preuves (par slide)

### Slide 1

Action live:
- Pas de commande (cadrage oral).

Preuve:
- Le jury comprend le plan en 3 étapes.

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
- Les services existent et la plateforme est déployée.

### Slide 4

Action live:
```bash
docker secret ls
docker service inspect nebula_users-api --format '{{json .Spec.TaskTemplate.ContainerSpec.Secrets}}'
```

Preuve:
- Secret présent et bien injecté dans les services.

### Slide 5

Action live:
```bash
docker node inspect ubuntu1-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu2-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu3-lefevret --format '{{ .Spec.Labels }}'
docker service ps nebula_edge-proxy
docker service ps nebula_users-api
docker service ps nebula_postgres
```

Preuve:
- Placement conforme à l’architecture.

### Slide 6

Action live:
```bash
docker service inspect nebula_users-api --format '{{json .Spec.UpdateConfig}}'
docker service inspect nebula_users-api --format '{{json .Spec.TaskTemplate.RestartPolicy}}'
```

Preuve:
- Config de résilience visible dans la spec du service.

### Slide 7

Action live:
```bash
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=nebula_edge-proxy | head -n 1)
docker rm -f "$CID"
sleep 3
docker service ps nebula_edge-proxy
```

Preuve:
- L’ancienne tâche est arrêtée et une nouvelle tâche est recréée.

### Slide 8

Action live:
```bash
sed -n '1,200p' deploy/swarm/base/stack.apps.yml
sed -n '1,200p' deploy/swarm/overlays/3vm-placement.yml
sed -n '1,200p' scripts/deploy/one-button-3vm.sh
```

Preuve:
- Le jury voit la logique de déploiement dans le code.

### Slide 9

Action live:
```bash
curl -i http://127.0.0.1/health
curl -i http://127.0.0.1/feed/user-1
```

Preuve:
- La plateforme répond toujours après les manipulations.

### Slide 10

Action live:
- Pas de commande obligatoire (slide de transition).

Preuve:
- Transition claire vers le PPT Terraform.
