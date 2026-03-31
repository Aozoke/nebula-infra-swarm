# Présentation Nebula — Script oral détaillé (10 slides)

Ce document te dit exactement quoi expliquer à l'oral, slide par slide.  
Il est aligné avec `docs/procedures/presentation-jury-12slides.md` (version 10 slides).

## Slide 1 — Problème et objectif

Ce que tu expliques:
- "Mon objectif n'était pas de faire un réseau social complet, mais de prouver une infrastructure microservices opérable."
- "Je devais démontrer un déploiement distribué, une communication inter-services fiable, et une exploitation réaliste."
- "Le livrable principal est donc une plateforme technique démontrable devant un jury."

Message de fin de slide:
- "Je vais vous montrer ce qui a été fait, validé, et ce qui reste pour la suite."

## Slide 2 — Topologie 3 VM et rôles

Ce que tu expliques:
- "J'ai travaillé sur un cluster 3 VM avec une séparation claire des responsabilités."
- "VM1 est manager et point d'entrée, VM2 exécute les services applicatifs, VM3 exécute les services de données."
- "Cette séparation permet de réduire les conflits et de mieux maîtriser l'exploitation."

Message de fin de slide:
- "Le design n'est pas juste théorique: il est appliqué dans le cluster."

## Slide 3 — Architecture des services

Ce que tu expliques:
- "Le point d'entrée HTTP est Traefik, puis les API métiers sont découplées par responsabilité."
- "Les données sont stockées dans Postgres, et Redis sert à la fois pour le stream d'événements et le cache feed."
- "Les réseaux overlay séparent l'exposition publique, la communication applicative, et la zone data."

Message de fin de slide:
- "L'architecture est volontairement simple, mais couvre les briques d'un vrai environnement."

## Slide 4 — Déploiement Swarm reproductible

Ce que tu expliques:
- "Le déploiement est piloté par des stacks séparées: data, edge et apps."
- "J'ai ajouté des stratégies de mise à jour et rollback pour éviter les coupures sur les services stateless."
- "L'objectif était de pouvoir rejouer le déploiement de façon fiable sans bricolage manuel."

Message de fin de slide:
- "On est sur une logique d'exploitation, pas juste sur un `docker run` local."

## Slide 5 — Placement contrôlé par labels

Ce que tu expliques:
- "J'ai utilisé des labels de nœuds pour forcer le placement par rôle."
- "Le proxy reste sur le nœud edge, les APIs tournent sur le nœud app, et Postgres/Redis restent sur le nœud data."
- "Ce point est important car il prouve que l'architecture cible est réellement appliquée."

Message de fin de slide:
- "La topologie n'est pas déclarative seulement, elle est respectée en exécution."

## Slide 6 — Parcours fonctionnel API (synchrone)

Ce que tu expliques:
- "Le parcours utilisateur commence par la création d'un user, puis la création d'un post."
- "Lors de la création du post, le service posts vérifie l'auteur via users-api."
- "Cette partie démontre que le routage et les appels inter-services synchrones fonctionnent."

Message de fin de slide:
- "On valide ici le fonctionnement API classique, avant la partie événementielle."

## Slide 7 — Asynchrone et cache (valeur technique)

Ce que tu expliques:
- "Après écriture du post, un événement `post.created` est publié dans Redis Streams."
- "Le worker consomme cet événement et construit la projection du feed."
- "Le feed-api lit ensuite cette projection avec cache Redis pour accélérer les lectures répétées."

Message de fin de slide:
- "C'est la partie clé du projet: flux découplé, observable et performant."

## Slide 8 — Persistance, secrets, exploitation

Ce que tu expliques:
- "La persistance est assurée par volume Postgres et AOF Redis."
- "Le secret DB est injecté via Docker secrets, donc pas stocké en clair dans le code."
- "J'ai aussi intégré des outils d'exploitation: Portainer pour la vue ops et registry privé pour fiabiliser la distribution d'images."

Message de fin de slide:
- "Ce sont des choix orientés run, pas seulement développement."

## Slide 9 — Incident réel et résolution

Ce que tu expliques:
- "J'ai rencontré un incident concret: les workers ne rejoignaient pas le swarm."
- "Le diagnostic a montré un problème MTU lié à VXLAN dans le lab."
- "Le correctif `mtu: 1400` a permis de stabiliser le join et de finaliser le cluster."

Message de fin de slide:
- "Ce point montre ma capacité à diagnostiquer et corriger un vrai problème infra."

## Slide 10 — Résultats, limites, suite

Ce que tu expliques:
- "Le résultat obtenu: cluster 3 nœuds opérationnel, placement conforme, flux end-to-end validé."
- "Côté réplication, les services applicatifs peuvent monter en replicas; la couche data reste en instance unique dans ce MVP."
- "La suite logique est claire: HA data, CI/CD, et provisioning Terraform complet pour recréer l'environnement de bout en bout."

Message de fin de slide:
- "En résumé, la base technique est solide et prête à être industrialisée."

---

## Conseils de delivery (oral)

- Rythme recommandé: 45 à 75 secondes par slide.
- Toujours terminer une slide par la valeur apportée, pas seulement par la technique.
- Utiliser le vocabulaire "ce qui est fait", "ce qui est prouvé", "ce qui est prévu ensuite".
