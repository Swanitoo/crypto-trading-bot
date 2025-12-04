import ccxt
from typing import Dict, List, Optional
from datetime import datetime
import logging
from ..utils.retry import retry_on_failure, ConnectionManager

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize Binance client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (paper trading) or live trading
        """
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 15000,  # 15 secondes timeout pour éviter les blocages
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True
            }
        })

        if testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("🧪 Binance client initialized in TESTNET mode")
        else:
            logger.info("⚠️  Binance client initialized in LIVE mode")

        self.testnet = testnet
        self.connection_manager = ConnectionManager()

    @retry_on_failure(max_attempts=3, initial_delay=1.0, exceptions=(ccxt.NetworkError, ccxt.ExchangeNotAvailable))
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get balance for a specific currency"""
        try:
            balance = self.exchange.fetch_balance()
            self.connection_manager.record_success()
            return balance['free'].get(currency, 0.0)
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:
            self.connection_manager.record_failure()
            raise
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0

    @retry_on_failure(max_attempts=3, initial_delay=1.0, exceptions=(ccxt.NetworkError, ccxt.ExchangeNotAvailable))
    def get_ticker(self, pair: str) -> Optional[Dict]:
        """Get current ticker information for a pair"""
        try:
            ticker = self.exchange.fetch_ticker(pair)
            self.connection_manager.record_success()
            return {
                'symbol': ticker['symbol'],
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['quoteVolume'],
                'change_24h': ticker['percentage'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:
            self.connection_manager.record_failure()
            raise
        except Exception as e:
            logger.error(f"Error fetching ticker for {pair}: {e}")
            return None

    @retry_on_failure(max_attempts=3, initial_delay=1.0, exceptions=(ccxt.NetworkError, ccxt.ExchangeNotAvailable))
    def get_ohlcv(self, pair: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Get OHLCV (candlestick) data

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            self.connection_manager.record_success()
            return [
                {
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as e:
            self.connection_manager.record_failure()
            raise
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {pair}: {e}")
            return []

    def create_market_buy_order(self, pair: str, amount: float) -> Optional[Dict]:
        """
        Create a market buy order

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            amount: Amount in quote currency (USDT)
        """
        try:
            order = self.exchange.create_market_buy_order(pair, amount)
            logger.info(f"✅ Market BUY order created: {pair} - {amount}")
            return {
                'id': order['id'],
                'symbol': order['symbol'],
                'type': order['type'],
                'side': order['side'],
                'price': order.get('price', 0),
                'amount': order['amount'],
                'cost': order['cost'],
                'filled': order['filled'],
                'status': order['status'],
                'timestamp': datetime.fromtimestamp(order['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error creating buy order for {pair}: {e}")
            return None

    def create_market_sell_order(self, pair: str, amount: float) -> Optional[Dict]:
        """
        Create a market sell order

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            amount: Amount of base currency to sell
        """
        try:
            order = self.exchange.create_market_sell_order(pair, amount)
            logger.info(f"✅ Market SELL order created: {pair} - {amount}")
            return {
                'id': order['id'],
                'symbol': order['symbol'],
                'type': order['type'],
                'side': order['side'],
                'price': order.get('price', 0),
                'amount': order['amount'],
                'cost': order['cost'],
                'filled': order['filled'],
                'status': order['status'],
                'timestamp': datetime.fromtimestamp(order['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error creating sell order for {pair}: {e}")
            return None

    def get_order_book(self, pair: str, limit: int = 20) -> Optional[Dict]:
        """Get order book for a pair"""
        try:
            order_book = self.exchange.fetch_order_book(pair, limit)
            timestamp = order_book.get('timestamp')
            return {
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {pair}: {e}")
            return None

    def get_markets(self) -> List[str]:
        """Get list of all available trading pairs"""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []


class PaperTradingClient:
    """Paper trading simulator - no real money involved"""

    def __init__(self, initial_balance: float = 100.0, db_session=None):
        self.db_session = db_session
        self.positions = {}
        self.order_history = []

        # Créer UNE SEULE instance ccxt pour toutes les requêtes (évite fuites mémoire)
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 15000  # 15 secondes timeout
        })

        # Load or initialize wallet from database
        self.balance = self._load_wallet_from_db(initial_balance)

        logger.info(f"📄 Paper trading initialized with {self.balance.get('USDT', 0):.2f} USDT")
        logger.info(f"   Total wallet value: {self._calculate_total_value():.2f} USDT")

    def get_balance(self, currency: str = 'USDT') -> float:
        return self.balance.get(currency, 0.0)

    def get_ticker(self, pair: str) -> Optional[Dict]:
        """Get real market data even in paper trading"""
        try:
            ticker = self.exchange.fetch_ticker(pair)
            return {
                'symbol': ticker['symbol'],
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['quoteVolume'],
                'change_24h': ticker['percentage'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {pair}: {e}")
            return None

    def get_ohlcv(self, pair: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get real OHLCV data even in paper trading"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            return [
                {
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {pair}: {e}")
            return []

    def create_market_buy_order(self, pair: str, amount_usdt: float) -> Optional[Dict]:
        """Simulate a market buy order"""
        try:
            ticker = self.get_ticker(pair)
            if not ticker:
                return None

            price = ticker['ask']
            amount_crypto = amount_usdt / price

            if self.balance.get('USDT', 0) < amount_usdt:
                logger.warning(f"Insufficient balance for buy order: {pair}")
                return None

            # Update balances
            self.balance['USDT'] -= amount_usdt
            base_currency = pair.split('/')[0]
            self.balance[base_currency] = self.balance.get(base_currency, 0) + amount_crypto

            # Update positions
            if pair not in self.positions:
                self.positions[pair] = {
                    'amount': 0,
                    'avg_price': 0,
                    'total_cost': 0
                }

            pos = self.positions[pair]
            pos['total_cost'] += amount_usdt
            pos['amount'] += amount_crypto
            pos['avg_price'] = pos['total_cost'] / pos['amount']

            order = {
                'id': f"paper_{len(self.order_history) + 1}",
                'symbol': pair,
                'type': 'market',
                'side': 'buy',
                'price': price,
                'amount': amount_crypto,
                'cost': amount_usdt,
                'filled': amount_crypto,
                'status': 'closed',
                'timestamp': datetime.now()
            }

            self.order_history.append(order)
            logger.info(f"📄 Paper BUY: {amount_crypto:.6f} {base_currency} at {price:.2f} USDT")

            # Save wallet to database
            self._save_wallet_to_db()

            return order

        except Exception as e:
            logger.error(f"Error in paper buy order: {e}")
            return None

    def create_market_sell_order(self, pair: str, amount: float) -> Optional[Dict]:
        """Simulate a market sell order"""
        try:
            ticker = self.get_ticker(pair)
            if not ticker:
                return None

            price = ticker['bid']
            base_currency = pair.split('/')[0]

            if self.balance.get(base_currency, 0) < amount:
                logger.warning(f"Insufficient {base_currency} for sell order")
                return None

            amount_usdt = amount * price

            # Update balances
            self.balance[base_currency] -= amount
            self.balance['USDT'] = self.balance.get('USDT', 0) + amount_usdt

            # Update positions
            if pair in self.positions:
                pos = self.positions[pair]
                pos['amount'] -= amount
                pos['total_cost'] -= (amount * pos['avg_price'])

                if pos['amount'] <= 0:
                    del self.positions[pair]

            order = {
                'id': f"paper_{len(self.order_history) + 1}",
                'symbol': pair,
                'type': 'market',
                'side': 'sell',
                'price': price,
                'amount': amount,
                'cost': amount_usdt,
                'filled': amount,
                'status': 'closed',
                'timestamp': datetime.now()
            }

            self.order_history.append(order)
            logger.info(f"📄 Paper SELL: {amount:.6f} {base_currency} at {price:.2f} USDT")

            # Save wallet to database
            self._save_wallet_to_db()

            return order

        except Exception as e:
            logger.error(f"Error in paper sell order: {e}")
            return None

    def _load_wallet_from_db(self, initial_balance: float) -> Dict[str, float]:
        """Load wallet state from database or initialize it"""
        from ..database.models import PaperWallet

        wallet = {}

        if not self.db_session:
            logger.warning("⚠️  No database session provided - wallet won't persist between restarts")
            return {'USDT': initial_balance}

        try:
            # Load all currencies from database
            wallet_entries = self.db_session.query(PaperWallet).all()

            if not wallet_entries:
                # First time - initialize wallet with USDT
                logger.info(f"💰 Initializing paper wallet with {initial_balance} USDT")
                usdt_entry = PaperWallet(
                    currency='USDT',
                    balance=initial_balance,
                    initial_balance=initial_balance
                )
                self.db_session.add(usdt_entry)
                self.db_session.commit()
                wallet['USDT'] = initial_balance
            else:
                # Load existing wallet
                for entry in wallet_entries:
                    wallet[entry.currency] = entry.balance

                logger.info(f"💰 Loaded paper wallet from database:")
                for currency, balance in wallet.items():
                    if balance > 0:
                        logger.info(f"   {currency}: {balance:.8f}")

            return wallet

        except Exception as e:
            logger.error(f"Error loading wallet from database: {e}")
            logger.warning(f"⚠️  Falling back to initial balance: {initial_balance} USDT")
            try:
                self.db_session.rollback()
            except:
                pass
            return {'USDT': initial_balance}

    def _save_wallet_to_db(self):
        """Save current wallet state to database"""
        from ..database.models import PaperWallet

        if not self.db_session:
            return

        try:
            for currency, balance in self.balance.items():
                # Check if entry exists
                entry = self.db_session.query(PaperWallet).filter(
                    PaperWallet.currency == currency
                ).first()

                if entry:
                    # Update existing entry
                    entry.balance = balance
                else:
                    # Create new entry
                    entry = PaperWallet(
                        currency=currency,
                        balance=balance,
                        initial_balance=0.0  # Only USDT has initial balance set
                    )
                    self.db_session.add(entry)

            self.db_session.commit()

        except Exception as e:
            logger.error(f"Error saving wallet to database: {e}")
            try:
                self.db_session.rollback()
            except:
                pass

    def _calculate_total_value(self) -> float:
        """Calculate total wallet value in USDT"""
        total = self.balance.get('USDT', 0.0)

        for currency, amount in self.balance.items():
            if currency == 'USDT' or amount == 0:
                continue

            try:
                pair = f"{currency}/USDT"
                ticker = self.get_ticker(pair)
                if ticker:
                    total += amount * ticker['price']
            except:
                pass

        return total

    def get_order_book(self, pair: str, limit: int = 20) -> Optional[Dict]:
        """Get real order book data"""
        try:
            order_book = self.exchange.fetch_order_book(pair, limit)
            timestamp = order_book.get('timestamp')
            return {
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {pair}: {e}")
            return None
