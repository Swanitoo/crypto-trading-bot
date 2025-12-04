# 💰 Gestion du Wallet Virtuel (Paper Trading)

Le wallet virtuel est maintenant **persistant** ! Il se comporte comme un vrai compte Binance : ton argent virtuel reste le même entre les redémarrages.

## 📋 Commandes disponibles

### 1. Voir l'état du wallet
```bash
./reset_wallet.sh info
```
Affiche :
- Balance de chaque devise (USDT, BTC, ETH, etc.)
- Montant initial et P&L total
- Nombre de trades ouverts/fermés

### 2. Reset le wallet uniquement
```bash
# Reset à 100 USDT (config par défaut)
./reset_wallet.sh reset

# Reset à un montant personnalisé
./reset_wallet.sh reset --amount 1000

# Sans confirmation
./reset_wallet.sh reset --amount 500 --yes
```
⚠️ Garde l'historique des trades mais reset le wallet

### 3. Reset complet (wallet + historique)
```bash
./reset_wallet.sh reset-all --amount 1000
```
⚠️⚠️⚠️ SUPPRIME TOUT : trades, sessions, wallet, etc.

### 4. Migrer la base de données
```bash
./migrate_db.sh
```
Ajoute les nouvelles tables sans perdre les données existantes.

## 🚀 Utilisation normale

### Premier démarrage
```bash
./run_bot.sh
```
Le wallet sera créé automatiquement avec le montant du `config/config.yaml` (actuellement 100 USDT).

### Redémarrages suivants
Le bot **récupère automatiquement** ton wallet :
- Même balance USDT
- Mêmes cryptos détenues
- Comme si c'était un vrai compte !

## 💡 Cas d'usage

### Scénario 1 : Trading normal
```bash
# Démarre le bot
./run_bot.sh

# Fait des trades...
# Arrête le bot
./stop_bot.sh

# Redémarre le bot plus tard
./run_bot.sh
# → Le wallet est récupéré automatiquement !
```

### Scénario 2 : Repartir sur une base propre
```bash
# Vérifier l'état actuel
./reset_wallet.sh info

# Reset uniquement le wallet (garde l'historique)
./reset_wallet.sh reset --amount 100

# Redémarrer le bot
./run_bot.sh
```

### Scénario 3 : Tout effacer et recommencer
```bash
# Reset complet
./reset_wallet.sh reset-all --amount 1000

# Redémarrer le bot
./run_bot.sh
```

## 📊 Exemple de sortie

### État du wallet
```
💰 Current paper wallet:
============================================================
   USDT: 45.23000000
      Initial: 100.00 USDT
      P&L: -54.77 USDT (-54.77%)
   BTC: 0.00085234
   ETH: 0.01245600
============================================================
   Total value: ~102.35 USDT

📊 Trading statistics:
   Open trades: 2
   Closed trades: 15
```

## ⚙️ Configuration

Le montant initial est défini dans `config/config.yaml` :
```yaml
trading:
  initial_balance: 100  # Montant en USDT
```

## 🔧 Troubleshooting

### Le wallet ne persiste pas
- Vérifier que la migration a été faite : `./migrate_db.sh`
- Vérifier les logs : `tail -f bot.log`

### Database is locked
```bash
# Tuer tous les processus
./stop_bot.sh

# Attendre 2-3 secondes
sleep 3

# Redémarrer
./run_bot.sh
```

### Reset ne fonctionne pas
```bash
# S'assurer que le bot est arrêté
./stop_bot.sh

# Lancer le reset
./reset_wallet.sh reset --yes
```

## 📝 Notes importantes

1. **Mode paper trading** : Le wallet persistant fonctionne uniquement en mode `paper` (simulation)
2. **Mode live** : En mode réel, c'est le vrai wallet Binance qui est utilisé
3. **Sauvegarde automatique** : Le wallet est sauvegardé après chaque trade
4. **Récupération automatique** : Le bot récupère le wallet au démarrage
