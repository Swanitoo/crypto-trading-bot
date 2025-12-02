# 🚀 Démarrage Rapide - 5 Minutes

## Étape 1 : Installation (2 min)

```bash
# Lancer le script d'installation
./setup.sh
```

Le script va :
- ✅ Créer l'environnement virtuel Python
- ✅ Installer toutes les dépendances
- ✅ Créer la structure de dossiers
- ✅ Copier le fichier de config exemple

## Étape 2 : Configuration (2 min)

```bash
# Éditer le fichier de configuration
nano config/.env
```

**Remplace** ces valeurs :

```env
# ⚡ OBLIGATOIRE - Ta clé OpenAI
OPENAI_API_KEY=sk-ta-vraie-clé-ici

# 📊 Mode de trading (paper = simulation, live = réel)
MODE=paper

# 💰 Solde de départ (en USDT/EUR)
INITIAL_BALANCE=10
```

> 💡 **Astuce** : Pour l'instant, laisse `MODE=paper` pour tester sans risque !

## Étape 3 : Test de Configuration (30 sec)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Tester la config
python test_config.py
```

Si tout est ✅ vert, tu es prêt !

## Étape 4 : Lancement ! (30 sec)

```bash
# Méthode 1 : Script rapide
./start.sh

# Méthode 2 : Python direct
python main.py
```

## Étape 5 : Ouvrir le Dashboard

Ouvre ton navigateur sur :
```
http://localhost:5000
```

Tu verras :
- 💰 Ton solde en temps réel
- 📊 Les graphiques de performance
- 🤖 Les analyses de l'IA
- 📈 Tes positions ouvertes
- 📜 L'historique de tes trades

## 🎮 Utilisation

### Contrôler le bot depuis le dashboard :

1. **▶️ Start** : Démarre le bot
2. **⏸️ Pause** : Met en pause (garde les positions ouvertes)
3. **⏹️ Stop** : Arrête complètement

### Le bot va automatiquement :

1. 🔍 Analyser les marchés toutes les 30 secondes
2. 🤖 Demander l'avis de l'IA toutes les 5 minutes
3. 📊 Calculer les indicateurs techniques (RSI, MACD, EMA)
4. 💹 Ouvrir des positions si les signaux sont forts
5. 🛡️ Gérer le risque avec stop-loss et take-profit
6. 📈 Mettre à jour le dashboard en temps réel

## ⚙️ Personnalisation Rapide

Édite `config/config.yaml` pour changer :

```yaml
trading:
  trade_amount: 5          # Montant par trade (€)
  max_positions: 2         # Positions max simultanées
  take_profit_percent: 5   # Objectif de gain (%)
  stop_loss_percent: 3     # Stop-loss (%)
  check_interval: 30       # Intervalle de vérification (secondes)

  pairs:                   # Paires à trader
    - BTC/USDT
    - ETH/USDT
    - BNB/USDT

strategy:
  use_ai: true            # Activer/désactiver l'IA
  ai_confidence_threshold: 70  # Seuil de confiance minimum (%)
```

## 🔧 Commandes Utiles

```bash
# Activer l'environnement (à faire à chaque fois)
source venv/bin/activate

# Lancer en mode debug (plus de logs)
python main.py --debug

# Lancer seulement le dashboard (sans auto-start)
python main.py --mode dashboard

# Lancer seulement en CLI (sans dashboard)
python main.py --mode cli

# Tester la configuration
python test_config.py
```

## 📊 Suivre les Performances

Le dashboard te montre en temps réel :

- **Balance** : Ton capital actuel
- **P&L** : Profit/Perte totale
- **Win Rate** : Pourcentage de trades gagnants
- **Positions** : Trades en cours
- **Historique** : Tous tes trades passés

Tout est sauvegardé dans `data/trading_bot.db`

## 🎯 Ton Objectif avec 10€

Avec ta config actuelle :
- **5€ par trade**
- **2 positions max**
- **+5% take profit** = gain de 0.25€ par trade réussi
- **-3% stop loss** = perte max de 0.15€ par trade raté

**Exemple réaliste** :
- 10 trades : 6 gagnants ✅ (+1.50€) + 4 perdants ❌ (-0.60€) = **+0.90€ profit**
- Soit **+9% de rendement**

## ⚠️ Conseils Importants

1. **Teste d'abord en paper trading** pendant au moins 2-3 jours
2. **Surveille le dashboard** régulièrement
3. **Commence petit** : 10€ c'est parfait pour apprendre
4. **Ne change pas les paramètres** trop souvent
5. **Sois patient** : Le bot n'est pas magique, il faut du temps

## 🐛 Problèmes Courants

### Le bot ne démarre pas
```bash
# Vérifier que l'environnement est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur "OpenAI API Key"
```bash
# Vérifier que la clé est dans .env
cat config/.env | grep OPENAI_API_KEY

# La clé doit commencer par "sk-"
```

### Le dashboard ne s'ouvre pas
```bash
# Vérifier que le port 5000 est libre
lsof -i :5000

# Ou changer de port
export FLASK_PORT=5001
python main.py
```

## 📈 Prochaines Étapes

1. ✅ Fais tourner le bot en mode paper pendant 2-3 jours
2. ✅ Analyse les résultats dans le dashboard
3. ✅ Ajuste les paramètres si nécessaire
4. ✅ Une fois confiant, passe en mode `live` avec un PETIT montant
5. ✅ Augmente progressivement si ça marche bien

## 💡 Tips & Tricks

### Optimiser les profits
- Monte le `take_profit_percent` si le marché est volatile
- Augmente `max_positions` si tu as plus de capital
- Teste différentes paires de trading

### Réduire les risques
- Baisse le `trade_amount`
- Monte le `ai_confidence_threshold`
- Utilise un `stop_loss_percent` plus serré

### Performances IA
- Le bot utilise GPT-4 par défaut (meilleur mais plus cher)
- Tu peux changer pour `gpt-3.5-turbo` dans `config/config.yaml`
- L'analyse IA coûte ~0.01$ par appel

---

**C'est parti ! 🚀**

Si tout fonctionne, tu devrais voir le bot analyser le marché et potentiellement faire ses premiers trades en mode paper !

Bon trading ! 💰
