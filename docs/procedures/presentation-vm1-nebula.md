# Présentation Nebula — Script oral (Partie 1 Docker Swarm)

Ce fichier te sert à dire exactement quoi raconter pendant la première partie de soutenance.  
Il suit le plan demandé:  
1) Présentation Swarm + réalisation + secrets + services + résilience  
2) Suppression pour test de résilience  
3) Analyse du code Docker Swarm

## Slide 1 — Plan de la première partie

Ici, je commence en annonçant clairement le déroulé en 3 étapes.  
D’abord je présente l’architecture Swarm et ce qu’on a réalisé.  
Ensuite je fais un test de résilience en supprimant un conteneur/service.  
Enfin je montre le code de déploiement Swarm pour expliquer comment c’est construit.

Phrase de transition:
"Je vais commencer par ce qui est en place et validé techniquement."

## Slide 2 — Docker Swarm et topologie cluster

J’explique que j’ai un cluster 3 VM avec séparation des rôles:  
VM1 manager/edge, VM2 app, VM3 data.

Je précise aussi la démarche:
j’ai commencé sur 1 VM pour valider le MVP, puis j’ai étendu en 3 VM pour démontrer une vraie topologie d’exploitation.

Phrase de transition:
"La séparation des rôles me permet de maîtriser le placement et la stabilité."

## Slide 3 — Ce que j’ai réalisé concrètement

Je raconte ce que j’ai construit:
les services Nebula, le déploiement en stack, et l’automatisation.

Point clé à dire:
j’ai créé un "bouton" de déploiement `scripts/deploy/one-button-3vm.sh`.  
Ce script applique les labels, déploie Nebula avec l’overlay 3 VM, déploie Portainer, puis lance un smoke test.

Pourquoi je l’ai fait:
pour avoir un déploiement reproductible et éviter les erreurs manuelles.

## Slide 4 — Gestion des secrets

J’explique que les secrets sensibles ne sont pas codés en dur dans les fichiers applicatifs.  
Le mot de passe Postgres est injecté via Docker secret, puis lu par les services via des variables `*_PASSWORD_FILE`.

Message important:
ce n’est pas un système de sécurité complet enterprise, mais c’est une bonne pratique minimale propre pour un MVP infra.

## Slide 5 — Services déployés et placement

Je liste les services principaux, puis j’explique le placement par labels.  
Le proxy est sur edge, les APIs sur app, la data sur data.

Ce que je veux faire comprendre:
le cluster ne "tourne pas au hasard"; l’architecture cible est appliquée volontairement.

## Slide 6 — Résilience native Swarm

Je présente la résilience attendue dans Swarm:
si une tâche tombe, l’orchestrateur doit recréer une tâche pour retrouver l’état désiré.

Je mentionne aussi les stratégies update/restart configurées sur les services stateless.

Phrase de transition:
"Maintenant je passe à la démonstration concrète: je supprime et je vérifie la reconstruction."

## Slide 7 — Test de résilience par suppression

Ici, je supprime volontairement un conteneur d’un service managé (ex: edge-proxy).  
Je montre ensuite que Swarm relance automatiquement une nouvelle tâche.

Message clé:
la résilience est prouvée en runtime, pas juste annoncée dans la doc.

## Slide 8 — Analyse du code Docker Swarm

Je bascule en lecture de code de déploiement:
- les stacks dans `deploy/swarm/base/`
- l’overlay de placement `deploy/swarm/overlays/3vm-placement.yml`
- les scripts d’automatisation dans `scripts/deploy/`

Ce que je dis:
on peut relire et comprendre la logique de déploiement, elle est versionnée et explicite.

## Slide 9 — Bilan de cette partie Swarm

Je résume ce qui est validé:
cluster opérationnel, services placés, secrets gérés, résilience testée, code de déploiement analysé.

Je peux conclure:
la plateforme est exploitable sur les VM existantes.

## Slide 10 — Transition vers la partie 2

Je précise que cette première partie couvre Docker Swarm sur l’existant.  
Le second PPT couvre Terraform: créer 3 nouvelles VM, récupérer le code sur Git, redéployer Nebula.

Phrase de clôture recommandée:
"Partie 1: j’ai validé l’exploitation Swarm. Partie 2: je vais valider la recréation de l’environnement de zéro."

---

## Conseils de delivery

- Reste en "je" pour montrer ta contribution réelle.
- Fais des phrases courtes: action -> résultat -> valeur.
- Évite de mélanger Terraform ici: garde la transition en fin de slide 10.
