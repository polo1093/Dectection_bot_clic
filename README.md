# Bot risk (browser game) — FastAPI + mouse dynamics (POC)

Objectif: afficher en overlay dans ton jeu navigateur une **probabilité de bot** (risk score 0–1) basée sur la cinématique des mouvements/clics.

⚠️ Notes produit
- Ce score est **probabiliste** et adversarial: il sert à déclencher de la friction / du contrôle additionnel, pas à bannir "en dur" dès le premier signal.
- Pour limiter les enjeux RGPD, l’exemple **n’envoie pas** les trajectoires brutes, uniquement des **features agrégées**.

## 1) Installation
```bash
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# Linux/mac:
# source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Lancer le serveur
```bash
uvicorn app:app --reload
```

Ouvre ensuite:
- Jeu/demo: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

## 3) Collecter des samples humains (pour entraîner)
Dans la page, clique sur **Collect human sample** (ça envoie la fenêtre de features au backend).
Après ~200–500 fenêtres, lance l'entraînement:

```bash
python train.py
```

Le modèle est sauvegardé dans `models/isoforest.joblib` + `models/calibration.json`.

## 4) Comment ça marche
- Front: capture `pointermove/pointerdown/pointerup` puis calcule des features (dt, vitesses, rectilinéarité, etc.).
- Backend: modèle d’anomalie (IsolationForest) entraîné sur **humains**; plus c’est "out-of-distribution", plus le score monte.

## 5) Intégration dans ton vrai jeu
- Copie `static/bot_risk.js` et appelle `BotRisk.start({ endpoint: "/api/score" })`
- Style overlay dans `static/style.css` (ou adapte ton HUD)
