# Geler les preuves (soutenance) — Cluster 3 VM

## Objectif
Capturer des preuves horodatées et reproductibles de l'état du cluster et du flux applicatif.

## Pré-requis
- Être sur le manager Swarm (`ubuntu1-lefevret`).
- Stack `nebula` déployée.
- Services en `1/1` (`docker stack services nebula`).

## Commande unique
```bash
cd /home/etudiant/Nebula-infra-swarm
./scripts/test/freeze-evidence-3vm.sh
```

## Résultat attendu
Un dossier est créé dans `docs/evidence/<timestamp>/` avec:
- état cluster (`docker node ls`)
- état stack (`docker stack services`)
- placement détaillé (`docker service ps`)
- logs des services clés (`docker service logs`)
- réponses HTTP complètes (`/health`, création user, création post, lecture feed)
- fichier de synthèse (`00-summary.txt`)

## Variante
Changer stack/url si besoin:
```bash
STACK_NAME=nebula BASE_URL=http://127.0.0.1 ./scripts/test/freeze-evidence-3vm.sh
```
