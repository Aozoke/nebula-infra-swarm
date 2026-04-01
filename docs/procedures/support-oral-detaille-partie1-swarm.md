# Support oral detaille - Partie 1 Docker Swarm

Ce document couvre uniquement la partie 1 de la soutenance:

- Docker Swarm
- services deployes
- secrets
- resilience
- analyse du code Swarm

La partie 2 Terraform / creation de nouvelles VM est geree dans un autre support.

Convention de demo:

- toutes les commandes de ce document sont lancees sur `VM1` (manager), sauf mention contraire
- `VM1=ubuntu1-lefevret (10.100.9.222)`
- `VM2=ubuntu2-lefevret (10.100.9.135)`
- `VM3=ubuntu3-lefevret (10.100.9.223)`

---

## Slide 1 - Titre / objectif de la partie 1

### Ce que je dis

"Dans cette premiere partie, je montre une exploitation Docker Swarm complete sur 3 VM existantes."

"Mon objectif etait d'obtenir un deploiement distribue, un flux fonctionnel bout en bout, et des preuves techniques verifiables en live."

"Je ne presente pas seulement des conteneurs qui tournent: je presente une methode de deploiement, des contraintes de placement, des secrets, et un test de resilience."

### Ce que je montre

- le depot `Nebula-infra-swarm`
- l'arborescence `deploy/` et `scripts/`
- le plan oral en 3 temps:
- 1) architecture et deploiement
- 2) test de resilience
- 3) lecture du code Swarm

### Commandes

```bash
cd /home/etudiant/Nebula-infra-swarm
pwd
ls
```

### Detail des commandes

- `cd /home/etudiant/Nebula-infra-swarm`: se place dans le bon repo pour eviter les erreurs de chemin.
- `pwd`: prouve en live que tu es bien dans le repo attendu.
- `ls`: affiche la structure racine (`deploy`, `scripts`, `services`, `docs`) que tu vas utiliser pendant la demo.

### Resultat attendu

- on voit clairement le repo de travail
- on confirme que la demo est faite depuis le manager

---

## Slide 2 - De 1 VM vers 3 VM (demarche)

### Ce que je dis

"Je suis parti d'un MVP sur 1 VM pour valider rapidement le socle applicatif."

"Ensuite, j'ai industrialise vers 3 VM pour separer les roles: edge/manager, app, data."

"Cette progression m'a permis de reduire le risque: d'abord prouver que ca marche, puis structurer le cluster."

### Ce que je montre

- la logique de migration 1 VM -> 3 VM
- la difference entre test local simple et exploitation cluster

### Commandes

```bash
docker node ls
docker stack services nebula
```

### Detail des commandes

- `docker node ls`: affiche les noeuds du cluster Swarm, leur statut, et qui est leader/manager.
- `docker stack services nebula`: affiche tous les services du stack `nebula` avec le ratio `REPLICAS` pour prouver l'etat global.

### Resultat attendu

- 3 noeuds `Ready`
- services `nebula_*` visibles dans le stack

---

## Slide 3 - Topologie cible et labels de placement

### Ce que je dis

"La topologie est volontairement simple et lisible:
VM1 manager+edge, VM2 worker app, VM3 worker data."

"Le respect de cette topologie est impose par labels de noeuds et contraintes de placement."

"Donc on n'est pas dans 'ca tourne quelque part', mais dans 'ca tourne au bon endroit'."

### Ce que je montre

- les labels appliques aux noeuds
- la correspondance role/noeud

### Commandes

```bash
docker node ls
docker node inspect ubuntu1-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu2-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu3-lefevret --format '{{ .Spec.Labels }}'
```

### Detail des commandes

- `docker node ls`: verifie que les 3 noeuds sont actifs avant de verifier les labels.
- `docker node inspect ... ubuntu1 ...`: montre le label edge/manager attribue a VM1.
- `docker node inspect ... ubuntu2 ...`: montre le label app attribue a VM2.
- `docker node inspect ... ubuntu3 ...`: montre le label data attribue a VM3.

### Resultat attendu

- VM1 avec `role=edge`
- VM2 avec `role=app`
- VM3 avec `role=data`

---

## Slide 4 - Architecture des services et des reseaux

### Ce que je dis

"J'ai decoupe le systeme en services specialises:
Traefik en entree, APIs metier, worker asynchrone, Postgres, Redis."

"J'ai separe les reseaux overlay `public`, `app`, `data` pour isoler les flux."

"Cette architecture couvre les patterns classiques: entree HTTP, logique metier, evenementiel, cache, persistance."

### Ce que je montre

- `deploy/swarm/base/stack.edge.yml`
- `deploy/swarm/base/stack.apps.yml`
- `deploy/swarm/base/stack.data.yml`

### Commandes

```bash
sed -n '1,220p' deploy/swarm/base/stack.edge.yml
sed -n '1,320p' deploy/swarm/base/stack.apps.yml
sed -n '1,220p' deploy/swarm/base/stack.data.yml
```

### Detail des commandes

- `sed -n '1,220p' ...stack.edge.yml`: affiche le proxy Traefik, le port 80 publie, et les options de provider Docker Swarm.
- `sed -n '1,320p' ...stack.apps.yml`: affiche les services applicatifs, variables d'environnement, labels Traefik, et policy de rollout/rollback.
- `sed -n '1,220p' ...stack.data.yml`: affiche Postgres/Redis, les volumes persistants, et le secret DB externe.

### Resultat attendu

- Traefik expose `:80`
- APIs sur reseaux `app` + `data`
- Postgres/Redis sur reseau `data`
- secret externe `nebula_postgres_password`

---

## Slide 5 - Le bouton de deploiement 3 VM

### Ce que je dis

"Apres la phase manuelle, j'ai cree un bouton de deploiement: `scripts/deploy/one-button-3vm.sh`."

"Ce script enchaine 4 etapes: label nodes, deploy Nebula, deploy Portainer, smoke retest."

"Objectif: rendre le deploiement reproductible, reduire les erreurs humaines, et pouvoir rejouer la meme procedure dans un autre environnement."

### Ce que je montre

- script `one-button-3vm.sh`
- script `label-nodes-3vm.sh`
- script `deploy-nebula-3vm.sh`

### Commandes

```bash
sed -n '1,220p' scripts/deploy/one-button-3vm.sh
sed -n '1,260p' scripts/deploy/label-nodes-3vm.sh
sed -n '1,220p' scripts/deploy/deploy-nebula-3vm.sh
```

### Detail des commandes

- `sed ... one-button-3vm.sh`: montre l'ordre d'execution global du bouton.
- `sed ... label-nodes-3vm.sh`: montre la logique de nettoyage des anciens labels et d'application des nouveaux labels edge/app/data.
- `sed ... deploy-nebula-3vm.sh`: montre le check manager, le check secret, puis le `docker stack deploy` avec overlays.

### Resultat attendu

- on voit clairement le pipeline de deploiement
- on voit le check manager + check secret avant deploy

---

## Slide 6 - Secrets, images et deploiement controle

### Ce que je dis

"Le secret DB n'est pas dans le code: il est injecte via Docker secret."

"Les services lisent le mot de passe via `DATABASE_PASSWORD_FILE` et `POSTGRES_PASSWORD_FILE`."

"Pour les images applicatives, j'ai gere deux modes:
mode local (image presente sur chaque noeud) et mode registry prive."

### Ce que je montre

- secret present dans Swarm
- deploiement Nebula par stacks
- etat final des services

### Commandes

```bash
docker secret ls
docker secret inspect nebula_postgres_password >/dev/null && echo "secret ok"
docker stack deploy --detach=false \
  -c deploy/swarm/base/stack.data.yml \
  -c deploy/swarm/base/stack.edge.yml \
  -c deploy/swarm/base/stack.apps.yml \
  -c deploy/swarm/overlays/3vm-placement.yml \
  nebula
docker stack services nebula
```

### Detail des commandes

- `docker secret ls`: liste tous les secrets disponibles dans Swarm.
- `docker secret inspect nebula_postgres_password ...`: verifie explicitement que le secret requis existe avant deploy.
- `docker stack deploy --detach=false ...`: deploie/maj le stack en restant attache a la convergence pour voir les erreurs en direct.
- `-c ...stack.data.yml`: charge la couche data (Postgres/Redis/volumes).
- `-c ...stack.edge.yml`: charge la couche edge (Traefik).
- `-c ...stack.apps.yml`: charge la couche applicative (users/posts/feed/worker).
- `-c ...3vm-placement.yml`: applique les contraintes de placement par labels.
- `nebula`: nom du stack cible.
- `docker stack services nebula`: verifie le resultat final en replicas.

### Resultat attendu

- secret `nebula_postgres_password` existe
- services `nebula_*` converges a `1/1`

---

## Slide 7 - Validation fonctionnelle bout en bout

### Ce que je dis

"Je valide le parcours metier complet:
health check, creation user, creation post, lecture feed."

"Le point important: `posts-api` depend de `users-api` pour verifier l'auteur, puis publie un evenement dans Redis Streams."

"`feed-worker` consomme cet evenement, ecrit en base, et `feed-api` renvoie le feed."

### Ce que je montre

- reponses HTTP reelles
- coherence des IDs `user-*` et `post-*`
- feed contenant le post cree

### Commandes

```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"jury-part1"}'
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"demo-part1"}'
sleep 2
curl -i http://127.0.0.1/feed/user-1
docker service logs --tail 40 nebula_feed-worker
```

### Detail des commandes

- `curl -i .../health`: test de sante du point d'entree HTTP.
- `curl -i -X POST .../users ...`: cree un utilisateur pour etablir une base de test.
- `curl -i -X POST .../posts ...`: cree un post, ce qui declenche la publication evenementielle.
- `sleep 2`: laisse le temps au worker de consommer l'evenement.
- `curl -i .../feed/user-1`: verifie que le post est bien visible dans le feed.
- `docker service logs --tail 40 nebula_feed-worker`: montre la consommation des evenements et la persistence cote worker.

### Resultat attendu

- `health` retourne `200`
- `POST /users` retourne `201`
- `POST /posts` retourne `201`
- `GET /feed/user-1` retourne un item avec `post_id`

---

## Slide 8 - Resilience: suppression volontaire d'un conteneur

### Ce que je dis

"Deuxieme etape de la soutenance: je casse volontairement un conteneur pour verifier la resilience."

"Swarm maintient un etat desire. Si une tache tombe, Swarm recree une nouvelle tache automatiquement."

"Je montre la preuve dans `docker service ps` avant/apres."

### Ce que je montre

- conteneur supprime manuellement
- nouvelle tache `Running`

### Commandes

```bash
docker service ps nebula_users-api
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=nebula_users-api | head -n 1)
docker rm -f "$CID"
sleep 3
docker service ps nebula_users-api
docker stack services nebula
```

### Detail des commandes

- `docker service ps nebula_users-api`: capture l'etat initial des taches avant action.
- `CID=$(docker ps -q --filter ... | head -n 1)`: recupere l'ID d'un conteneur de ce service.
- `docker rm -f "$CID"`: supprime de force le conteneur pour simuler un incident.
- `sleep 3`: laisse le scheduler recreer la tache.
- `docker service ps nebula_users-api`: montre la recreation automatique d'une nouvelle tache.
- `docker stack services nebula`: verifie que le service revient a `1/1`.

### Resultat attendu

- ancienne tache en `Shutdown` / `Failed`
- nouvelle tache `Running`
- service reste a `1/1`

---

## Slide 9 - Incident reel rencontre: MTU/VXLAN

### Ce que je dis

"On a eu un vrai incident: `swarm join` en timeout alors que les ports semblaient ouverts."

"Le diagnostic a mene a une contrainte MTU avec VXLAN. La correction a ete `mtu: 1400` sur les interfaces Ubuntu."

"Apres correction, le join worker a reussi et le cluster 3 noeuds est devenu stable."

### Ce que je montre

- test ping MTU
- interface reseau avec MTU 1400
- join Swarm reussi

### Commandes

```bash
ip link show eth0 | grep mtu
ping -M do -s 1450 10.100.9.222 || true
ping -M do -s 1372 10.100.9.222
sudo docker swarm leave --force || true
sudo docker swarm join --token <WORKER_TOKEN> --advertise-addr 10.100.9.223 --data-path-addr 10.100.9.223 10.100.9.222:2377
docker node ls
```

### Detail des commandes

- `ip link show eth0 | grep mtu`: affiche la MTU effective de l'interface.
- `ping -M do -s 1450 ...`: test un paquet trop gros en mode "do not fragment" pour detecter le blocage MTU.
- `ping -M do -s 1372 ...`: test une taille compatible pour confirmer l'hypothese MTU.
- `sudo docker swarm leave --force || true`: nettoie l'etat Swarm local si necessaire avant retry.
- `sudo docker swarm join ...`: retente le join worker avec adresses explicites.
- `docker node ls`: valide cote manager que le noeud rejoint bien le cluster.

### Resultat attendu

- MTU affiche `1400`
- ping gros paquet echoue avant correction puis passe avec taille adaptee
- join worker affiche `This node joined a swarm as a worker.`

---

## Slide 10 - Bilan, limites, transition partie 2

### Ce que je dis

"Bilan partie 1:
cluster 3 noeuds operationnel, deploiement structure, secrets, placement, test fonctionnel et resilience valides."

"Limites assumees a ce stade:
base data en instance unique, pas encore de pipeline CI/CD complet, et provisioning infra pas encore one-shot."

"La partie 2 (Terraform) prendra le relais: creer de nouvelles VM puis redeployer le meme socle automatiquement."

### Ce que je montre

- tableau court `Fait / Limites / Suite`
- lien vers le support Terraform

### Commandes

```bash
docker node ls
docker stack services nebula
docker service ps nebula_users-api
```

### Detail des commandes

- `docker node ls`: rappel final de la sante cluster.
- `docker stack services nebula`: rappel final de la convergence des services.
- `docker service ps nebula_users-api`: preuve detaillee de l'historique des taches apres test resilience.

### Resultat attendu

- tout le socle de la partie 1 est demonstrable en direct

---

## Points pratiques a retenir (Partie 1)

- lancer les commandes cluster uniquement depuis un manager Swarm
- verifier le secret avant deploy: `nebula_postgres_password`
- verifier les labels avant deploy pour eviter `no suitable node`
- utiliser le script bouton pour limiter les erreurs manuelles
- valider toujours en 3 blocs: etat cluster, test metier, test resilience

---

## Annexe finale - commandes exactes jour J (Partie 1)

### 1. Positionnement

```bash
cd /home/etudiant/Nebula-infra-swarm
docker info --format 'Swarm manager={{.Swarm.ControlAvailable}}'
```

### 2. Verifier le cluster

```bash
docker node ls
docker node inspect ubuntu1-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu2-lefevret --format '{{ .Spec.Labels }}'
docker node inspect ubuntu3-lefevret --format '{{ .Spec.Labels }}'
```

### 3. Verifier le secret et deployer

```bash
docker secret inspect nebula_postgres_password >/dev/null || printf '<PASSWORD>' | docker secret create nebula_postgres_password -
scripts/deploy/one-button-3vm.sh ubuntu1-lefevret ubuntu2-lefevret ubuntu3-lefevret
docker stack services nebula
```

### 4. Test fonctionnel

```bash
curl -i http://127.0.0.1/health
curl -i -X POST http://127.0.0.1/users -H 'Content-Type: application/json' -d '{"handle":"jury-live"}'
curl -i -X POST http://127.0.0.1/posts -H 'Content-Type: application/json' -d '{"author_id":"user-1","content":"jury-live-post"}'
sleep 2
curl -i http://127.0.0.1/feed/user-1
```

### 5. Test resilience

```bash
docker service ps nebula_users-api
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=nebula_users-api | head -n 1)
docker rm -f "$CID"
sleep 3
docker service ps nebula_users-api
docker stack services nebula
```

### 6. Analyse code live

```bash
sed -n '1,220p' deploy/swarm/base/stack.apps.yml
sed -n '1,220p' deploy/swarm/overlays/3vm-placement.yml
sed -n '1,220p' scripts/deploy/one-button-3vm.sh
sed -n '1,200p' services/feed-api/app/main.py
```

