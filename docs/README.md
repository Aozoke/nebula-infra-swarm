# Documentation Nebula

Ce dossier est structuré pour séparer clairement:
- l'architecture cible,
- les supports de soutenance,
- les plans/tests de validation,
- les pistes d'évolution.

## Structure

- `architecture/`
  - `cluster-topology.md`: rôles VM, IP, labels, placement.
- `procedures/`
  - `presentation-jury-12slides.md`: version courte prête pour PPT/Gamma.
  - `presentation-vm1-nebula.md`: version détaillée (notes longues).
  - `code-walkthrough-main-py.md`: explication technique des services Python.
  - `manipulations-completes.md`: runbook complet des commandes.
- `tests/`
  - `freeze-evidence-3vm.md`: gel des preuves de soutenance.
  - `retest-plan-3vm.md`: plan de re-test.
- `evolution/`
  - `README.md`: roadmap/axes d'amélioration.

## Utilisation recommandée pour la soutenance

1. Construire le support visuel avec `procedures/presentation-jury-12slides.md`.
2. Garder `procedures/presentation-vm1-nebula.md` comme support oral détaillé.
3. Utiliser `procedures/manipulations-completes.md` pendant les répétitions techniques.

