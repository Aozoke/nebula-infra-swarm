# Présentation Nebula — Script oral naturel (10 slides)

Ce fichier est ton texte de préparation oral, en mode "je raconte ce que j'ai fait".  
Version visuelle (Gamma/PPT): `docs/procedures/presentation-jury-12slides.md`.

## Slide 1 — Problème et objectif

Ici, je pose le cadre: je n'ai pas voulu faire une application complète, j'ai voulu prouver que je sais monter une infrastructure microservices exploitable.  
Mon objectif, c'était d'avoir un déploiement distribué, un flux fonctionnel bout-en-bout, et des preuves concrètes de fonctionnement.

Transition:
"Donc la question, ce n'est pas le design produit, c'est: est-ce que la plateforme tient techniquement."

## Slide 2 — Topologie 3 VM et rôles

Mon architecture cible est en 3 VM avec des rôles séparés.  
VM1 gère le cluster et l'entrée réseau, VM2 exécute les services applicatifs, VM3 héberge les services de données.

Important à dire:
j'ai commencé par faire fonctionner le MVP sur une seule VM, puis j'ai étendu vers 3 VM pour valider la vraie logique d'exploitation.

Transition:
"Donc je suis parti simple, puis j'ai industrialisé progressivement."

## Slide 3 — Architecture des services

J'ai découpé les briques en services spécialisés: Traefik pour l'entrée, des APIs métier, un worker asynchrone, Postgres, Redis.  
J'ai aussi séparé les réseaux overlay (`public`, `app`, `data`) pour isoler les responsabilités.

Ce que je veux faire comprendre:
le découpage est volontairement sobre, mais il couvre les patterns d'une infra réelle: entrée, métier, données, asynchrone, cache.

## Slide 4 — De 1 VM à un bouton de déploiement 3 VM

Après la phase MVP sur VM1, j'ai créé un "bouton" de déploiement pour éviter les manipulations manuelles répétitives.  
Le bouton principal est `scripts/deploy/one-button-3vm.sh`.

Comment il fonctionne:
il prend les 3 nœuds en arguments, applique les labels, déploie la stack Nebula avec overlay de placement, déploie Portainer, puis lance un smoke test.

Pourquoi je l'ai fait:
pour rendre le déploiement reproductible, réduire les erreurs humaines, et pouvoir rejouer la même procédure dans un autre environnement.

Note complémentaire:
j'ai aussi `scripts/deploy/one-button-full.sh` qui enchaîne en plus registry + monitoring.

## Slide 5 — Placement contrôlé par labels

Pour garantir que l'architecture est respectée, je place les services par labels de nœuds (`role=edge`, `role=app`, `role=data`).  
Concrètement, le proxy reste sur edge, les APIs et le worker sur app, et Postgres/Redis sur data.

Ce que je veux démontrer ici:
ce n'est pas juste "ça tourne", c'est "ça tourne au bon endroit".

## Slide 6 — Parcours API synchrone

Ensuite, je valide le parcours fonctionnel de base: santé, création utilisateur, création post.  
Le point important est que `posts-api` vérifie bien l'auteur via `users-api`, donc j'ai déjà une vraie dépendance inter-service synchrone.

Message à faire passer:
l'API répond, et les interactions entre services sont cohérentes.

## Slide 7 — Flux asynchrone et cache

Après la création du post, l'événement part dans Redis Streams.  
Le worker le consomme pour alimenter la projection feed, puis le `feed-api` lit cette projection avec cache Redis.

Ce que j'explique clairement:
je n'ai pas juste des endpoints HTTP, j'ai aussi un flux événementiel + cache observables en logs.

## Slide 8 — Persistance, secrets et exploitation

J'ai sécurisé le minimum vital: secret DB hors code via Docker secret.  
J'ai assuré la persistance avec volume Postgres et AOF Redis.

Côté exploitation, j'ai ajouté Portainer pour la visibilité et un registry privé pour distribuer les images dans le cluster sans dépendre du build local.

## Slide 9 — Incident réel rencontré et corrigé

J'ai eu un problème concret de `swarm join` qui bloquait malgré une connectivité apparente.  
Le diagnostic a montré une contrainte MTU liée à VXLAN; le passage à `mtu: 1400` a débloqué la situation.

Ce que je veux valoriser:
j'ai rencontré un incident d'infra réel, et je l'ai résolu de manière méthodique.

## Slide 10 — Ce qu’il manque et pourquoi on fait un 2e PPT

Là, je clos clairement la première partie:  
j'ai validé l'infra Nebula sur les 3 VM existantes, avec déploiement, placement et flux applicatif.

Ensuite, je liste ce qu'il manque encore:
la haute disponibilité data (Postgres/Redis), la chaîne CI/CD complète, et l'automatisation de provisioning infra.

Et là je fais la transition explicite:  
le prochain PPT sera dédié à la suite, c'est-à-dire la création de 3 nouvelles VM via Terraform, puis le redéploiement complet Nebula sur ces nouvelles VM.

Phrase de clôture recommandée:
"Cette première soutenance valide la base opérationnelle; la suivante montrera l'industrialisation de bout en bout."

---

## Conseils de delivery

- Parle en "je" pour montrer ce que tu as réellement fait.
- Termine chaque slide par la valeur apportée (fiabilité, reproductibilité, exploitabilité).
- Si on te challenge sur la réplication: "HA applicative validée, HA data prévue en itération suivante."
