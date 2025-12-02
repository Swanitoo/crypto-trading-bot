# 🤖 Crypto Trading Bot

Un bot de trading de cryptomonnaies sophistiqué avec analyse par IA, indicateurs techniques, gestion des risques et dashboard web en temps réel.

## ✨ Fonctionnalités

### 🧠 Intelligence Artificielle
- **Analyse de marché par OpenAI GPT-4** : Le bot utilise l'IA pour analyser les conditions du marché
- **Recommandations avec niveau de confiance** : Chaque décision est accompagnée d'un score de confiance
- **Raisonnement détaillé** : L'IA explique ses recommandations

### 📊 Analyse Technique
- **Indicateurs multiples** : RSI, MACD, EMA, Bollinger Bands
- **Détection de tendance** : Identification automatique des tendances haussières/baissières
- **Support et résistance** : Calcul automatique des niveaux clés

### 🛡️ Gestion des Risques
- **Stop-Loss automatique** : Protection contre les pertes importantes
- **Take-Profit automatique** : Sécurisation des gains
- **Limite de positions simultanées** : Évite la surexposition
- **Limite de perte quotidienne** : Arrête le trading en cas de mauvaise journée

### 📈 Dashboard Web en Temps Réel
- **Visualisation du solde et P&L** : Graphiques en temps réel
- **Positions ouvertes** : Vue détaillée de toutes les positions actives
- **Historique des trades** : Tous vos trades avec statistiques
- **Analyse IA en direct** : Voir les recommandations de l'IA
- **Contrôle du bot** : Start/Pause/Stop depuis l'interface

### 💰 Modes de Trading
- **Paper Trading** : Mode simulation sans argent réel (parfait pour débuter!)
- **Live Trading** : Trading réel sur Binance

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- Compte Binance (uniquement pour le live trading)
- Clé API OpenAI

### Installation rapide

```bash
# Cloner le projet (si nécessaire)
cd crypto-trading-bot

# Rendre le script d'installation exécutable
chmod +x setup.sh

# Lancer l'installation
./setup.sh
```

### Installation manuelle

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate  # Sur Windows

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Configurer les clés API

Copier le fichier d'exemple et le remplir :

```bash
cp config/.env.example config/.env
```

Éditer `config/.env` :

```env
# Binance API (optionnel pour paper trading)
BINANCE_API_KEY=votre_clé_api_binance
BINANCE_API_SECRET=votre_secret_binance

# OpenAI API (OBLIGATOIRE)
OPENAI_API_KEY=sk-votre_clé_openai

# Configuration du bot
MODE=paper  # paper ou live
INITIAL_BALANCE=10  # Solde de départ en USDT

# Flask (optionnel)
FLASK_SECRET_KEY=votre_clé_secrète_random
FLASK_PORT=5000
```

### 2. Configurer les paramètres de trading

Éditer `config/config.yaml` pour personnaliser :

```yaml
trading:
  mode: paper  # paper ou live
  initial_balance: 10  # Solde de départ
  pairs:
    - BTC/USDT
    - ETH/USDT
    - BNB/USDT
  trade_amount: 5  # Montant par trade
  max_positions: 2  # Nombre max de positions simultanées
  take_profit_percent: 5  # Objectif de profit (%)
  stop_loss_percent: 3  # Stop-loss (%)
  check_interval: 30  # Intervalle de vérification (secondes)

strategy:
  use_ai: true  # Activer l'analyse IA
  ai_confidence_threshold: 70  # Seuil de confiance minimum
  indicators:
    - RSI
    - MACD
    - EMA
  rsi_oversold: 30
  rsi_overbought: 70

ai:
  model: gpt-4-turbo-preview
  temperature: 0.3
  max_tokens: 500
  analysis_interval: 300  # Intervalle d'analyse IA (secondes)
```

## 🎮 Utilisation

### Mode Dashboard (Recommandé)

Lance le bot avec l'interface web :

```bash
python main.py
```

Ouvre ton navigateur sur : **http://localhost:5000**

Le dashboard te permet de :
- ✅ Démarrer/Arrêter/Mettre en pause le bot
- 📊 Voir ton solde et tes profits en temps réel
- 📈 Visualiser tes positions ouvertes
- 📜 Consulter l'historique de tes trades
- 🤖 Voir les analyses de l'IA

### Mode CLI uniquement

Lance le bot en ligne de commande :

```bash
python main.py --mode cli
```

### Options avancées

```bash
# Dashboard uniquement (sans auto-start du bot)
python main.py --mode dashboard

# Mode debug
python main.py --debug

# Fichier de config personnalisé
python main.py --config ma_config.yaml
```

## 📊 Structure du Projet

```
crypto-trading-bot/
├── main.py                 # Point d'entrée
├── requirements.txt        # Dépendances Python
├── setup.sh               # Script d'installation
├── config/
│   ├── .env.example       # Exemple de configuration
│   └── config.yaml        # Configuration du bot
├── src/
│   ├── bot/
│   │   ├── trader.py      # Orchestrateur principal
│   │   ├── strategy.py    # Stratégies de trading
│   │   └── risk_manager.py # Gestion des risques
│   ├── ai/
│   │   └── market_analyzer.py # Analyse IA
│   ├── exchange/
│   │   └── binance_client.py # Client Binance
│   ├── database/
│   │   └── models.py      # Modèles de données
│   └── web/
│       ├── app.py         # Application Flask
│       ├── templates/     # Templates HTML
│       └── static/        # CSS/JS
└── data/
    └── trading_bot.db     # Base de données SQLite
```

## 🔒 Sécurité

### ⚠️ IMPORTANT - Paper Trading d'abord !

**Commence TOUJOURS en mode paper trading** avant d'utiliser de l'argent réel :

1. ✅ Mode `paper` dans la config
2. ✅ Teste pendant plusieurs jours
3. ✅ Analyse les performances
4. ✅ Ajuste les paramètres
5. ⚠️ Seulement après : passe en mode `live` avec un PETIT montant

### 🛡️ Protection des clés API

- ❌ **JAMAIS** commiter le fichier `.env`
- ❌ **JAMAIS** partager tes clés API
- ✅ Utilise les restrictions IP sur Binance
- ✅ Active l'authentification 2FA

### 💡 Bonnes Pratiques

1. **Commence petit** : Teste avec 10€ comme prévu
2. **Surveille régulièrement** : Vérifie le dashboard souvent
3. **Ajuste les paramètres** : Affine les stop-loss et take-profit
4. **Garde des logs** : La base de données conserve tout l'historique
5. **Ne risque jamais plus que ce que tu peux perdre**

## 📈 Stratégies de Trading

Le bot utilise une approche hybride :

### 1. Analyse Technique
- **RSI** : Détecte les conditions de surachat/survente
- **MACD** : Identifie les changements de momentum
- **EMA** : Détecte les tendances

### 2. Analyse IA
- GPT-4 analyse les données du marché
- Considère les indicateurs techniques
- Évalue le risque/rendement
- Fournit une recommandation avec confiance

### 3. Système de Vote
- Chaque signal a un poids
- Les signaux sont agrégés
- Action seulement si confiance > seuil

## 🎯 Objectif avec 10€

Avec ton budget de 10€ et les paramètres par défaut :

- **Trade Amount** : 5€ par position
- **Max Positions** : 2 positions max
- **Take Profit** : 5% par trade
- **Stop Loss** : 3% maximum

### Scénario optimiste
- 2 trades gagnants : +10% → 11€
- 4 trades gagnants : +20% → 12€
- 10 trades gagnants : +50% → 15€

### Risques réels
- Frais de trading : ~0.2% par trade
- Volatilité du marché
- Les pertes sont possibles
- Le bot n'est pas magique !

## 🤖 Comment ça marche ?

1. **Collecte de données** : Le bot récupère les prix et volumes en temps réel
2. **Calcul d'indicateurs** : RSI, MACD, EMA sont calculés
3. **Analyse IA** : GPT-4 analyse le marché (toutes les 5 min par défaut)
4. **Génération de signal** : Vote entre indicateurs techniques et IA
5. **Gestion du risque** : Vérification des limites et du capital
6. **Exécution** : Passage d'ordres si signal fort
7. **Surveillance** : Monitoring des positions ouvertes (stop-loss/take-profit)

## 🐛 Dépannage

### Le bot ne démarre pas
```bash
# Vérifier l'environnement virtuel
source venv/bin/activate

# Vérifier les dépendances
pip install -r requirements.txt

# Vérifier les logs
python main.py --debug
```

### Erreur "OpenAI API Key not found"
```bash
# Vérifier que le fichier .env existe
ls config/.env

# Vérifier que la clé est définie
cat config/.env | grep OPENAI_API_KEY
```

### Le dashboard ne s'affiche pas
```bash
# Vérifier que le port n'est pas utilisé
lsof -i :5000

# Changer le port si nécessaire
export FLASK_PORT=5001
python main.py
```

### Erreur de connexion Binance
- En mode `paper`, les clés Binance ne sont pas nécessaires
- Le bot utilise les données réelles mais simule les trades
- Vérifie que tu es bien en mode `paper` dans la config

## 📚 Ressources

- [Documentation Binance API](https://binance-docs.github.io/apidocs/)
- [Documentation OpenAI](https://platform.openai.com/docs)
- [Documentation ccxt](https://docs.ccxt.com/)
- [Analyse Technique](https://www.investopedia.com/technical-analysis-4689657)

## 🚨 Avertissement

⚠️ **Ce bot est un projet éducatif et expérimental.**

- Le trading de cryptomonnaies comporte des risques importants
- Les performances passées ne garantissent pas les résultats futurs
- Ne trade jamais plus que ce que tu peux te permettre de perdre
- L'IA peut se tromper, les indicateurs techniques ne sont pas infaillibles
- Utilise ce bot à tes propres risques

## 📝 Licence

Ce projet est fourni "tel quel" sans garantie d'aucune sorte.

## 🙋 Support

Pour toute question ou problème :
1. Vérifie la section "Dépannage" ci-dessus
2. Regarde les logs avec `--debug`
3. Vérifie que ta configuration est correcte

---

**Bon trading ! 🚀💰**

N'oublie pas : commence en mode paper, teste, apprends, puis décide si tu veux utiliser de l'argent réel.
