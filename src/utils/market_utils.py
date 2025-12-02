import ccxt
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

def get_top_pairs(limit: int = 10, quote_currency: str = 'USDT') -> List[str]:
    """
    Récupère les top N paires par volume sur Binance

    Args:
        limit: Nombre de paires à récupérer (défaut: 10)
        quote_currency: Devise de cotation (défaut: USDT)

    Returns:
        Liste des paires (ex: ['BTC/USDT', 'ETH/USDT', ...])
    """
    try:
        exchange = ccxt.binance({'enableRateLimit': True})

        # Charger tous les marchés
        markets = exchange.load_markets()

        # Liste des stablecoins à exclure
        stablecoins = ['USDC', 'USDT', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'USDP', 'USDD', 'USDK']

        # Filtrer pour ne garder que les paires USDT actives (sans stablecoins)
        usdt_pairs = [
            symbol for symbol, market in markets.items()
            if market['quote'] == quote_currency
            and market['active']
            and market['spot']  # Seulement le spot trading
            and market['base'] not in stablecoins  # Exclure les stablecoins
        ]

        # Récupérer les tickers pour avoir le volume
        logger.info(f"Récupération du volume pour {len(usdt_pairs)} paires...")
        tickers = exchange.fetch_tickers(usdt_pairs)

        # Trier par volume (quoteVolume = volume en USDT)
        pairs_with_volume = []
        for symbol, ticker in tickers.items():
            if ticker.get('quoteVolume'):
                pairs_with_volume.append((symbol, ticker['quoteVolume']))

        # Trier par volume décroissant
        pairs_with_volume.sort(key=lambda x: x[1], reverse=True)

        # Prendre le top N
        top_pairs = [pair[0] for pair in pairs_with_volume[:limit]]

        logger.info(f"✅ Top {limit} paires récupérées:")
        for i, (pair, volume) in enumerate(pairs_with_volume[:limit], 1):
            logger.info(f"   {i}. {pair} - Volume: ${volume:,.0f}")

        return top_pairs

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du top {limit}: {e}")
        # Fallback sur les paires par défaut
        return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']

def get_top_pairs_info(limit: int = 10) -> List[Tuple[str, float, float]]:
    """
    Récupère les top N paires avec leur info (volume, prix)

    Returns:
        Liste de tuples (symbol, volume, price)
    """
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        markets = exchange.load_markets()

        usdt_pairs = [
            symbol for symbol, market in markets.items()
            if market['quote'] == 'USDT'
            and market['active']
            and market['spot']
        ]

        tickers = exchange.fetch_tickers(usdt_pairs)

        pairs_info = []
        for symbol, ticker in tickers.items():
            if ticker.get('quoteVolume') and ticker.get('last'):
                pairs_info.append((
                    symbol,
                    ticker['quoteVolume'],
                    ticker['last']
                ))

        pairs_info.sort(key=lambda x: x[1], reverse=True)

        return pairs_info[:limit]

    except Exception as e:
        logger.error(f"Erreur: {e}")
        return []
