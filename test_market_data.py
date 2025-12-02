#!/usr/bin/env python3
"""
Script de test pour vérifier que les données de marché fonctionnent
sans clé API Binance en mode paper trading
"""

import ccxt
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

def test_public_api():
    """Test que l'API publique Binance fonctionne sans clés"""

    print(f"{Fore.CYAN}{'='*60}")
    print(f"Test des Données de Marché (API Publique)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    # Initialiser Binance SANS clés API
    exchange = ccxt.binance({
        'enableRateLimit': True
    })

    pairs_to_test = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

    for pair in pairs_to_test:
        print(f"\n{Fore.YELLOW}📊 Test: {pair}{Style.RESET_ALL}")

        try:
            # Test 1: Récupérer le ticker
            ticker = exchange.fetch_ticker(pair)

            print(f"{Fore.GREEN}✅ Ticker récupéré:{Style.RESET_ALL}")
            print(f"   Prix: ${ticker['last']:,.2f}")
            print(f"   Volume 24h: ${ticker['quoteVolume']:,.0f}")
            print(f"   Variation: {ticker['percentage']:+.2f}%")

            # Test 2: Récupérer OHLCV
            ohlcv = exchange.fetch_ohlcv(pair, '1h', limit=5)

            print(f"{Fore.GREEN}✅ OHLCV récupéré:{Style.RESET_ALL}")
            print(f"   Derniers 5 chandeliers (1h):")
            for candle in ohlcv[-3:]:
                timestamp = candle[0] / 1000
                close = candle[4]
                print(f"   - Close: ${close:,.2f}")

        except Exception as e:
            print(f"{Fore.RED}❌ Erreur: {e}{Style.RESET_ALL}")
            return False

    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"✅ TOUS LES TESTS PASSÉS !")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    print(f"{Fore.CYAN}📝 Résultat:{Style.RESET_ALL}")
    print(f"   Les données de marché fonctionnent SANS clé API")
    print(f"   Le paper trading utilisera ces données réelles")
    print(f"   Aucune clé Binance nécessaire en mode 'paper'\n")

    return True

if __name__ == '__main__':
    try:
        success = test_public_api()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrompu{Style.RESET_ALL}")
        exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Erreur fatale: {e}{Style.RESET_ALL}")
        exit(1)
