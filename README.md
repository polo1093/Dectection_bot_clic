# Bot risk (browser game) — FastAPI + click-driven scoring (POC)

Objectif : afficher dans un jeu navigateur un **risk score bot (0–1)** basé sur :
- **mouse/pointer dynamics** (mouvements + clics sur une fenêtre glissante)
- **signaux d’automatisation** côté navigateur (ex: `navigator.webdriver`)

Le score est recalculé :
- **à chaque clic**
- et **automatiquement** si aucun clic depuis la dernière MAJ (idle refresh)
- en utilisant une **fenêtre glissante de 10 secondes** de mouvements/clics

> Ce projet est un POC “risk scoring” (probabiliste), pas un anti-cheat certifiant.

**NO TRAINING** : pas de pipeline d’entraînement, pas de datasets, pas de modèles ML sauvegardés.
Seules des heuristiques locales sont utilisées côté API.

---

## Principes produit

- **Adversarial** : un bot avancé peut imiter des trajectoires humaines. Le score sert à déclencher de la friction (rate-limit, step-up), pas à bannir directement.
- **Privacy-by-design** : le front ne transmet pas la trajectoire brute, seulement des **features agrégées**.
- **Décision** : évite le binaire. Utilise des seuils et/ou une agrégation temporelle (EMA) si nécessaire.

---

## Installation

```bash
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# Linux/mac:
# source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer le serveur

```bash
python run_server.py
```

Ou directement via Uvicorn :

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## API

- `POST /api/score` : scoring heuristique.
- `GET /api/health` : healthcheck.

Aucun endpoint `/api/train` ou `/api/collect/human` n’est fourni ni requis.
