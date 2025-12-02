# 🎮 Guide d'Utilisation Rapide

## 🚀 Commandes Principales

### Démarrer le Bot

```bash
./run_bot.sh
```

Le bot démarre en arrière-plan et le dashboard est accessible sur **http://localhost:5000**

### Arrêter le Bot

```bash
./stop_bot.sh
```

### Voir le Statut

```bash
./status_bot.sh
```

Affiche si le bot tourne et les dernières activités.

### Voir les Logs en Direct

```bash
tail -f bot.log
```

Appuie sur `Ctrl+C` pour quitter.

---

## 📊 Dashboard Web

Une fois le bot lancé, ouvre ton navigateur sur :

```
http://localhost:5000
```

### Contrôles du Dashboard

- **▶️ Start** : Démarre le trading automatique
- **⏸️ Pause** : Met en pause (garde les positions ouvertes)
- **⏹️ Stop** : Arrête le trading (ferme les positions)

### Sections du Dashboard

1. **💰 Balance** : Ton capital actuel et disponible
2. **📊 Profit/Loss** : Gains/pertes totaux
3. **📈 Performance** : Statistiques (win rate, trades)
4. **⚠️ Risk Metrics** : Positions ouvertes, limites
5. **📉 Balance History** : Graphique d'évolution
6. **📍 Open Positions** : Positions en cours avec P&L live
7. **📜 Recent Trades** : Historique des trades
8. **🤖 AI Analysis** : Recommandations de l'IA

---

## 🔧 Configuration

### Modifier les Paramètres de Trading

Édite le fichier `config/config.yaml` :

```bash
nano config/config.yaml
```

**Paramètres clés** :

```yaml
trading:
  trade_amount: 5          # Montant par trade (€)
  take_profit_percent: 5   # Objectif de profit (%)
  stop_loss_percent: 3     # Stop-loss (%)
  max_positions: 2         # Positions max simultanées
  check_interval: 30       # Vérification toutes les 30 secondes

  pairs:                   # Paires à trader
    - BTC/USDT
    - ETH/USDT
    - BNB/USDT

strategy:
  use_ai: true            # Activer/désactiver l'IA
  ai_confidence_threshold: 70  # Seuil de confiance (0-100)
```

### Modifier les Clés API

Édite le fichier `config/.env` :

```bash
nano config/.env
```

```env
# OpenAI API (OBLIGATOIRE)
OPENAI_API_KEY=sk-ta-clé-ici

# Binance API (optionnel en mode paper)
BINANCE_API_KEY=ta-clé
BINANCE_API_SECRET=ton-secret

# Mode de trading
MODE=paper  # paper ou live
```

**⚠️ IMPORTANT** : Redémarre le bot après avoir modifié la config !

```bash
./stop_bot.sh
./run_bot.sh
```

---

## 📈 Workflow Typique

### Jour 1 : Test en Paper Trading

```bash
# 1. S'assurer que MODE=paper dans config/.env
cat config/.env | grep MODE

# 2. Lancer le bot
./run_bot.sh

# 3. Ouvrir le dashboard
open http://localhost:5000

# 4. Cliquer sur "▶️ Start" dans le dashboard

# 5. Surveiller les trades
tail -f bot.log
```

### Jour 2-3 : Analyse des Résultats

```bash
# Voir le statut
./status_bot.sh

# Consulter tous les logs
less bot.log

# Analyser la base de données
sqlite3 data/trading_bot.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

### Jour 4+ : Ajustements

Si les résultats sont bons :
- Ajuste `take_profit_percent` / `stop_loss_percent`
- Ajoute/retire des paires de trading
- Modifie `ai_confidence_threshold`

### Passage en Mode Live (⚠️ ATTENTION)

**Seulement après plusieurs jours de tests réussis** :

```bash
# 1. Arrêter le bot
./stop_bot.sh

# 2. Ajouter tes clés Binance dans config/.env
nano config/.env

# 3. Changer le mode
MODE=live

# 4. Sauvegarder et relancer
./run_bot.sh

# 5. SURVEILLER CONSTAMMENT
tail -f bot.log
```

---

## 🛠️ Maintenance

### Sauvegarder tes Données

```bash
# Sauvegarder la base de données
cp data/trading_bot.db data/backup_$(date +%Y%m%d).db

# Sauvegarder la config
cp config/.env config/.env.backup
```

### Nettoyer les Logs

```bash
# Voir la taille du log
du -h bot.log

# Archiver les anciens logs
mv bot.log bot_$(date +%Y%m%d).log

# Ou supprimer
rm bot.log
```

### Mettre à Jour les Dépendances

```bash
source venv/bin/activate
pip install --upgrade openai ccxt flask
```

---

## 🐛 Problèmes Courants

### Le bot ne démarre pas

```bash
# Vérifier la config
python test_config.py

# Voir les erreurs
cat bot.log
```

### Le dashboard ne répond pas

```bash
# Vérifier que le bot tourne
./status_bot.sh

# Vérifier le port
lsof -i :5000

# Redémarrer
./stop_bot.sh && ./run_bot.sh
```

### Pas de trades

Possible si :
- Confiance de l'IA < 70%
- Pas de signaux forts
- Maximum de positions atteint
- Marché trop calme

**Solution** : Baisse `ai_confidence_threshold` dans la config.

### Trop de pertes

**Solutions** :
- Monte `ai_confidence_threshold` (plus sélectif)
- Réduis `trade_amount`
- Resserre `stop_loss_percent`
- Change les paires de trading

---

## 📊 Analyser les Performances

### Via le Dashboard

Regarde :
- **Win Rate** : Doit être > 50%
- **Profit Factor** : Doit être > 1.0
- **Total P&L** : Évolution du capital

### Via la Base de Données

```bash
# Se connecter à la DB
sqlite3 data/trading_bot.db

# Voir tous les trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 20;

# Stats des trades fermés
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
    AVG(profit_loss_percent) as avg_pnl
FROM trades
WHERE status = 'closed';

# Meilleure et pire trade
SELECT pair, profit_loss, profit_loss_percent, timestamp
FROM trades
WHERE status = 'closed'
ORDER BY profit_loss DESC LIMIT 5;

# Sortir
.exit
```

---

## 💡 Tips & Astuces

### Optimiser les Coûts OpenAI

L'IA analyse toutes les 5 minutes par défaut. Pour économiser :

```yaml
# Dans config/config.yaml
ai:
  analysis_interval: 600  # 10 minutes au lieu de 5
```

### Trading Nocturne

Le bot tourne 24/7. Si tu veux le limiter à certaines heures, utilise cron :

```bash
# Démarrer à 9h
0 9 * * * cd /path/to/bot && ./run_bot.sh

# Arrêter à 18h
0 18 * * * cd /path/to/bot && ./stop_bot.sh
```

### Notifications

Tu peux ajouter des notifications (Telegram, Discord, etc.) en modifiant `src/bot/trader.py`.

### Backtesting

Pour tester une stratégie sur des données historiques, utilise les données OHLCV de Binance avec pandas.

---

## 🎯 Objectifs Réalistes

### Avec 10€ Initial

**Semaine 1** (apprentissage) :
- Objectif : +0% à +10%
- Focus : Comprendre le bot

**Semaine 2-4** (optimisation) :
- Objectif : +10% à +30%
- Focus : Ajuster les paramètres

**Mois 2+** (performance) :
- Objectif : +20% à +50% par mois
- Focus : Stabilité et régularité

**⚠️ Rappel** : Ces objectifs ne sont PAS garantis. Le trading comporte des risques.

---

## 📞 Support

Si tu rencontres des problèmes :

1. ✅ Lis ce guide
2. ✅ Vérifie `bot.log`
3. ✅ Lance `python test_config.py`
4. ✅ Vérifie que ta clé OpenAI a du crédit
5. ✅ Redémarre le bot

---

**Bon trading ! 🚀💰**

N'oublie pas : patience, discipline et gestion des risques sont les clés du succès !
