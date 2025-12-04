import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from colorama import Fore, Style

from ..exchange.binance_client import BinanceClient, PaperTradingClient
from ..ai.market_analyzer import MarketAnalyzer
from .strategy import TradingStrategy
from .risk_manager import RiskManager
from ..database.models import init_db, Trade, Balance, AIAnalysis
from ..utils.market_utils import get_top_pairs

logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot orchestrator"""

    def __init__(self, config: Dict, api_keys: Dict):
        """
        Initialize trading bot

        Args:
            config: Configuration dictionary
            api_keys: API keys for Binance and OpenAI
        """
        self.config = config
        self.running = False
        self.paused = False

        # Initialize database
        self.db_session = init_db()

        # Initialize components
        logger.info("🤖 Initializing Trading Bot...")

        # Exchange client
        mode = config['trading']['mode']
        if mode == 'paper':
            self.exchange = PaperTradingClient(
                initial_balance=config['trading']['initial_balance']
            )
        else:
            self.exchange = BinanceClient(
                api_key=api_keys['binance_api_key'],
                api_secret=api_keys['binance_api_secret'],
                testnet=False
            )

        # AI Analyzer (optional)
        self.use_ai = config['strategy'].get('use_ai', True)
        if self.use_ai:
            self.ai_analyzer = MarketAnalyzer(
                api_key=api_keys['openai_api_key'],
                model=config['ai']['model']
            )
        else:
            self.ai_analyzer = None

        # Trading parameters - Récupération des paires d'abord
        pairs_config = config['trading']['pairs']

        # Gestion du mode AUTO pour récupérer le top 10
        if pairs_config == 'auto':
            auto_count = config['trading'].get('auto_pairs_count', 10)
            logger.info(f"📊 Mode AUTO activé: récupération du top {auto_count} par volume...")
            self.pairs = get_top_pairs(limit=auto_count)
        elif isinstance(pairs_config, list):
            self.pairs = pairs_config
        else:
            logger.warning(f"Configuration pairs invalide: {pairs_config}")
            self.pairs = ['BTC/USDT']  # Fallback

        # Ajuster max_positions si mode auto
        trading_config = config['trading'].copy()
        if trading_config.get('max_positions') == 'auto':
            trading_config['max_positions'] = len(self.pairs)
            logger.info(f"📊 max_positions auto: {len(self.pairs)} (1 par paire)")

        # Strategy and risk management (après avoir défini les pairs)
        self.strategy = TradingStrategy(config['strategy'])
        self.risk_manager = RiskManager(trading_config)

        self.trade_amount = config['trading']['trade_amount']
        self.check_interval = config['trading']['check_interval']
        self.ai_analysis_interval = config['ai'].get('analysis_interval', 300)

        # State
        self.last_ai_analysis = {}
        self.last_ai_analysis_time = {}

        # Synchronize positions from database (in case of bot restart)
        self._sync_positions_from_db()

        # Initial balance snapshot
        self._save_balance_snapshot()

        logger.info(f"✅ Trading Bot initialized successfully")
        logger.info(f"   Mode: {mode.upper()}")
        logger.info(f"   Pairs: {', '.join(self.pairs)}")
        logger.info(f"   Trade Amount: ${self.trade_amount}")

    def start(self):
        """Start the trading bot"""
        self.running = True
        logger.info(f"\n{Fore.GREEN}{'='*60}")
        logger.info(f"🚀 TRADING BOT STARTED")
        logger.info(f"{'='*60}{Style.RESET_ALL}\n")

        try:
            while self.running:
                if not self.paused:
                    self._trading_loop()

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\n⏸️  Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        logger.info(f"\n{Fore.YELLOW}{'='*60}")
        logger.info(f"🛑 TRADING BOT STOPPED")
        logger.info(f"{'='*60}{Style.RESET_ALL}\n")

        # Close database session
        if self.db_session:
            self.db_session.close()

    def pause(self):
        """Pause the trading bot"""
        self.paused = True
        logger.info("⏸️  Trading bot paused")

    def resume(self):
        """Resume the trading bot"""
        self.paused = False
        logger.info("▶️  Trading bot resumed")

    def _trading_loop(self):
        """Main trading logic loop"""
        logger.info(f"\n{Fore.CYAN}--- Trading Loop [{datetime.now().strftime('%H:%M:%S')}] ---{Style.RESET_ALL}")

        for pair in self.pairs:
            try:
                self._process_pair(pair)
            except Exception as e:
                logger.error(f"Error processing {pair}: {e}", exc_info=True)
                # Continue avec les autres paires même en cas d'erreur
                continue

        # Save balance snapshot
        try:
            self._save_balance_snapshot()
        except Exception as e:
            logger.error(f"Error in balance snapshot: {e}")

        # Forcer le garbage collector toutes les 10 itérations pour éviter les fuites mémoire
        import gc
        if not hasattr(self, '_loop_count'):
            self._loop_count = 0
        self._loop_count += 1
        if self._loop_count % 10 == 0:
            gc.collect()
            logger.debug(f"Garbage collection executed (loop {self._loop_count})")

    def _process_pair(self, pair: str):
        """Process a single trading pair"""
        logger.info(f"\n📊 Analyzing {pair}...")

        # Get market data
        ticker = self.exchange.get_ticker(pair)
        if not ticker:
            logger.warning(f"Could not fetch ticker for {pair}")
            return

        ohlcv = self.exchange.get_ohlcv(pair, timeframe='1h', limit=100)
        if not ohlcv or len(ohlcv) < 50:
            logger.warning(f"Insufficient OHLCV data for {pair}")
            return

        # Calculate technical indicators
        indicators = self.strategy.calculate_indicators(ohlcv)
        if not indicators:
            logger.warning(f"Could not calculate indicators for {pair}")
            return

        # Get AI analysis (if enabled and interval passed)
        ai_analysis = None
        if self.use_ai:
            ai_analysis = self._get_ai_analysis(pair, ohlcv, indicators)

        # Generate trading signal
        signal = self.strategy.generate_signal(indicators, ai_analysis)

        logger.info(f"   Signal: {signal['action'].upper()} (Confidence: {signal['confidence']:.1f}%)")
        logger.info(f"   Reasoning: {signal['reasoning']}")

        # Check if we have an open position
        if self.risk_manager.has_position(pair):
            self._manage_open_position(pair, ticker['price'])
        else:
            self._evaluate_new_position(pair, signal, ticker['price'])

    def _get_ai_analysis(self, pair: str, ohlcv: List[Dict], indicators: Dict) -> Optional[Dict]:
        """Get AI analysis for a pair (with caching)"""
        current_time = time.time()
        last_analysis_time = self.last_ai_analysis_time.get(pair, 0)

        # Check if we need new analysis
        if current_time - last_analysis_time < self.ai_analysis_interval:
            return self.last_ai_analysis.get(pair)

        # Get fresh AI analysis
        logger.info("🤖 Requesting AI analysis...")

        try:
            order_book = self.exchange.get_order_book(pair)
        except Exception as e:
            logger.warning(f"Could not fetch order book for {pair}: {e}")
            order_book = None

        try:
            analysis = self.ai_analyzer.analyze_market(
                pair=pair,
                ohlcv_data=ohlcv,
                technical_indicators=indicators,
                order_book=order_book
            )
        except Exception as e:
            logger.error(f"AI analysis failed for {pair}: {e}")
            return None

        # Cache the analysis
        self.last_ai_analysis[pair] = analysis
        self.last_ai_analysis_time[pair] = current_time

        # Save to database
        try:
            ai_record = AIAnalysis(
                pair=pair,
                recommendation=analysis['recommendation'],
                confidence=analysis['confidence'],
                reasoning=analysis['reasoning']
            )
            self.db_session.add(ai_record)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Error saving AI analysis: {e}")

        return analysis

    def _manage_open_position(self, pair: str, current_price: float):
        """Manage an open position"""
        position = self.risk_manager.update_position(pair, current_price)

        if not position:
            return

        pnl_color = Fore.GREEN if position['profit_loss'] > 0 else Fore.RED
        logger.info(f"   📈 Open Position: "
                   f"{pnl_color}${position['profit_loss']:.2f} ({position['profit_loss_percent']:+.2f}%){Style.RESET_ALL}")

        # Check if partial TP triggered
        if position.get('partial_tp_triggered', False):
            tp_level = position['partial_tp_level']
            sell_percent = position['partial_tp_sell_percent']
            logger.info(f"   🎯 Partial TP Level +{tp_level}% reached! Selling {sell_percent}%...")
            self._execute_partial_exit(pair, current_price, sell_percent, tp_level)
            return  # Ne pas vérifier le close complet après une sortie partielle

        # Check if position should be closed completely
        should_close, reason = self.risk_manager.should_close_position(pair, current_price)

        if should_close:
            logger.info(f"   🔔 Closing position: {reason}")
            self._close_position(pair, current_price, reason)

    def _evaluate_new_position(self, pair: str, signal: Dict, current_price: float):
        """Evaluate opening a new position OR accumulating (DCA)"""
        # SECURITY: Never trade stablecoins (they don't move in price)
        STABLECOINS = ['USDC', 'USDT', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'USDP', 'USDD', 'USDK']
        base_currency = pair.split('/')[0]
        if base_currency in STABLECOINS:
            logger.warning(f"   ⛔ {pair} is a stablecoin - trading forbidden")
            return

        # Only open position if signal is strong enough
        min_confidence = 40  # Baissé à 40% pour être plus agressif
        if signal['confidence'] < min_confidence:
            logger.info(f"   ⏸️  Signal too weak (< {min_confidence}%)")
            return

        if signal['action'] not in ['buy', 'sell']:
            logger.info(f"   ⏸️  No action signal")
            return

        # For now, we only support long positions (buy)
        if signal['action'] != 'buy':
            logger.info(f"   ⏸️  Short selling not supported yet")
            return

        # Check if we can open position OR accumulate (DCA)
        balance = self.exchange.get_balance('USDT')
        can_trade, reason = self.risk_manager.can_open_position(balance, self.trade_amount, pair=pair)

        if not can_trade:
            logger.warning(f"   ❌ Cannot open position: {reason}")
            return

        # Check if this is DCA accumulation
        if self.risk_manager.has_position(pair):
            should_accumulate, dca_reason = self.risk_manager.should_accumulate(pair, current_price)
            if should_accumulate:
                logger.info(f"   🔄 DCA Accumulation opportunity: {dca_reason}")
                self._open_position(pair, current_price, signal)
            else:
                logger.info(f"   ⏸️  DCA not triggered: {dca_reason}")
        else:
            # Open new position
            logger.info(f"   ✅ Opening NEW BUY position for {pair}")
            self._open_position(pair, current_price, signal)

    def _open_position(self, pair: str, entry_price: float, signal: Dict):
        """Open a new trading position with adaptive TP/SL"""
        try:
            # Execute buy order
            order = self.exchange.create_market_buy_order(pair, self.trade_amount)

            if not order:
                logger.error(f"Failed to create buy order for {pair}")
                return

            # Get adaptive parameters from signal
            adaptive_params = signal.get('adaptive_params', {})
            take_profit_percent = adaptive_params.get('take_profit_percent', 3.0)
            stop_loss_percent = adaptive_params.get('stop_loss_percent', 2.0)
            market_context = signal.get('market_context', 'unknown')

            logger.info(f"   📊 Context: {market_context} | TP: {take_profit_percent}% | SL: {stop_loss_percent}%")

            # Open position in risk manager with adaptive TP/SL and fees
            amount = order['amount']
            position = self.risk_manager.open_position(
                pair=pair,
                entry_price=entry_price,
                amount=amount,
                side='long',
                custom_tp_percent=take_profit_percent,
                custom_sl_percent=stop_loss_percent,
                trade_amount_usd=self.trade_amount
            )

            # Save trade to database
            try:
                trade = Trade(
                    pair=pair,
                    side='buy',
                    amount=amount,
                    price=entry_price,
                    total=self.trade_amount,
                    status='open',
                    strategy=signal.get('reasoning', 'N/A'),
                    ai_confidence=signal.get('confidence', 0),
                    notes=f"Context: {market_context} | SL: ${position['stop_loss']:.2f}, TP: ${position['take_profit']:.2f}"
                )
                self.db_session.add(trade)
                self.db_session.commit()

                logger.info(f"   💾 Trade saved to database (ID: {trade.id})")

            except Exception as e:
                logger.error(f"Error saving trade to database: {e}")

        except Exception as e:
            logger.error(f"Error opening position: {e}")

    def _close_position(self, pair: str, exit_price: float, reason: str):
        """Close an open trading position"""
        try:
            position = self.risk_manager.get_position(pair)
            if not position:
                return

            # Execute sell order
            amount = position['amount']
            order = self.exchange.create_market_sell_order(pair, amount)

            if not order:
                logger.error(f"Failed to create sell order for {pair}")
                return

            # Close position in risk manager
            closed_position = self.risk_manager.close_position(pair, exit_price, reason)

            # Update trade in database
            try:
                trade = self.db_session.query(Trade).filter(
                    Trade.pair == pair,
                    Trade.status == 'open'
                ).order_by(Trade.timestamp.desc()).first()

                if trade:
                    trade.status = 'closed'
                    trade.profit_loss = closed_position['profit_loss']
                    trade.profit_loss_percent = closed_position['profit_loss_percent']
                    trade.notes = f"{trade.notes} | Exit: {reason}"
                    self.db_session.commit()

                    logger.info(f"   💾 Trade updated in database")

            except Exception as e:
                logger.error(f"Error updating trade in database: {e}")

        except Exception as e:
            logger.error(f"Error closing position: {e}")

    def _execute_partial_exit(self, pair: str, exit_price: float, sell_percent: float, tp_level: float):
        """Execute a partial exit (sell portion of position)"""
        try:
            # Get exit info from risk manager
            exit_info = self.risk_manager.partial_exit(pair, exit_price, sell_percent, tp_level)

            if not exit_info:
                logger.error(f"Failed to prepare partial exit for {pair}")
                return

            # Execute sell order
            amount_to_sell = exit_info['amount_to_sell']
            order = self.exchange.create_market_sell_order(pair, amount_to_sell)

            if not order:
                logger.error(f"Failed to create partial sell order for {pair}")
                return

            # Save partial exit as a separate trade in database
            try:
                partial_trade = Trade(
                    pair=pair,
                    side='sell',
                    amount=amount_to_sell,
                    price=exit_price,
                    total=exit_info['partial_profit'] + exit_info['sell_fees'],  # Proceeds from sale
                    status='closed',
                    profit_loss=exit_info['partial_profit'],
                    profit_loss_percent=exit_info['partial_profit_percent'],
                    strategy=f"Partial TP Level {tp_level}%",
                    notes=f"Partial exit: {sell_percent}% sold, {exit_info['remaining_amount']:.8f} remaining"
                )
                self.db_session.add(partial_trade)
                self.db_session.commit()

                logger.info(f"   💾 Partial exit saved to database (ID: {partial_trade.id})")

            except Exception as e:
                logger.error(f"Error saving partial exit to database: {e}")

        except Exception as e:
            logger.error(f"Error executing partial exit: {e}")

    def _sync_positions_from_db(self):
        """
        Synchronize open positions from database to risk manager.
        This is called on bot startup to restore positions after a restart.
        """
        try:
            # Liste des stablecoins à exclure
            STABLECOINS = ['USDC', 'USDT', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'USDP', 'USDD', 'USDK']

            # Get all open trades from database
            open_trades = self.db_session.query(Trade).filter(
                Trade.status == 'open',
                Trade.side == 'buy'  # Only long positions for now
            ).all()

            if not open_trades:
                logger.info("📊 No open positions to restore from database")
                return

            logger.info(f"🔄 Synchronizing {len(open_trades)} open positions from database...")

            # Group trades by pair (in case of duplicates)
            trades_by_pair = {}
            for trade in open_trades:
                if trade.pair not in trades_by_pair:
                    trades_by_pair[trade.pair] = []
                trades_by_pair[trade.pair].append(trade)

            # For each pair, keep only the most recent trade and close the rest
            restored_count = 0
            closed_count = 0

            for pair, trades in trades_by_pair.items():
                # Check if pair is a stablecoin (should never be traded)
                base_currency = pair.split('/')[0]
                if base_currency in STABLECOINS:
                    logger.warning(f"⚠️  {pair} is a stablecoin - closing all trades")
                    for trade in trades:
                        trade.status = 'closed'
                        trade.profit_loss = 0.0
                        trade.profit_loss_percent = 0.0
                        trade.notes = f"{trade.notes or ''} | Auto-closed: Stablecoin".strip()
                        closed_count += 1
                        logger.info(f"   ❌ Closed stablecoin trade ID {trade.id} for {pair}")
                    continue
                if len(trades) > 1:
                    # Sort by timestamp descending (most recent first)
                    trades.sort(key=lambda t: t.timestamp, reverse=True)

                    # Keep the most recent trade
                    most_recent = trades[0]
                    duplicates = trades[1:]

                    logger.warning(f"⚠️  Found {len(duplicates)} duplicate trades for {pair}")

                    # Close duplicates
                    for dup_trade in duplicates:
                        dup_trade.status = 'closed'
                        dup_trade.profit_loss = 0.0
                        dup_trade.profit_loss_percent = 0.0
                        dup_trade.notes = f"{dup_trade.notes or ''} | Auto-closed: Duplicate on restart".strip()
                        closed_count += 1
                        logger.info(f"   ❌ Closed duplicate trade ID {dup_trade.id} for {pair}")

                    # Restore the most recent one
                    trade = most_recent
                else:
                    trade = trades[0]

                # Get current price to calculate current P&L
                ticker = self.exchange.get_ticker(pair)
                if not ticker:
                    logger.warning(f"⚠️  Could not fetch current price for {pair} - closing position (pair may be delisted)")
                    trade.status = 'closed'
                    trade.profit_loss = 0.0
                    trade.profit_loss_percent = 0.0
                    trade.notes = f"{trade.notes or ''} | Auto-closed: Pair unavailable".strip()
                    closed_count += 1
                    continue

                current_price = ticker['price']

                # Calculate current P&L to check if position should be auto-closed
                entry_price = trade.price
                pnl_percent = ((current_price - entry_price) / entry_price) * 100

                # Auto-close positions with massive losses (> -20%) - likely dead coins
                if pnl_percent < -20:
                    logger.warning(f"⚠️  {pair} has {pnl_percent:.2f}% loss - auto-closing dead position")
                    trade.status = 'closed'
                    trade.exit_price = current_price
                    trade.profit_loss = (current_price - entry_price) * trade.amount
                    trade.profit_loss_percent = pnl_percent
                    trade.notes = f"{trade.notes or ''} | Auto-closed: Dead coin ({pnl_percent:.2f}%)".strip()
                    closed_count += 1
                    logger.info(f"   ❌ Closed dead position: {pair} (loss: {pnl_percent:.2f}%)")
                    continue

                # Auto-close positions for pairs not in current trading list
                if pair not in self.pairs:
                    logger.warning(f"⚠️  {pair} not in current trading pairs - auto-closing")
                    trade.status = 'closed'
                    trade.exit_price = current_price
                    trade.profit_loss = (current_price - entry_price) * trade.amount
                    trade.profit_loss_percent = pnl_percent
                    trade.notes = f"{trade.notes or ''} | Auto-closed: Not in trading list".strip()
                    closed_count += 1
                    logger.info(f"   ❌ Closed position: {pair} (not in trading list)")
                    continue

                # Restore position in risk manager
                position = self.risk_manager.open_position(
                    pair=pair,
                    entry_price=trade.price,
                    amount=trade.amount,
                    side='long'
                )

                # Restore crypto holdings in paper trading wallet
                # This is CRITICAL to avoid "Insufficient crypto" errors when selling
                if hasattr(self.exchange, 'balance'):  # Paper trading mode
                    base_currency = pair.split('/')[0]

                    # Add crypto to wallet
                    current_crypto = self.exchange.balance.get(base_currency, 0.0)
                    self.exchange.balance[base_currency] = current_crypto + trade.amount

                    # Deduct USDT that was used for this position
                    self.exchange.balance['USDT'] -= trade.total

                    logger.info(f"   💰 Restored wallet: +{trade.amount:.8f} {base_currency}, -{trade.total:.2f} USDT")

                # Update position with current price
                self.risk_manager.update_position(pair, current_price)

                restored_count += 1
                logger.info(f"   ✅ Restored position: {pair} @ ${trade.price:.2f} (current: ${current_price:.2f})")

            # Commit database changes (closing duplicates/stablecoins)
            if closed_count > 0:
                self.db_session.commit()
                logger.info(f"🧹 Closed {closed_count} duplicate/orphaned/stablecoin trades")

            logger.info(f"✅ Successfully restored {restored_count} positions from database")

        except Exception as e:
            logger.error(f"Error synchronizing positions from database: {e}")
            try:
                self.db_session.rollback()
            except:
                pass

    def _save_balance_snapshot(self):
        """Save current balance snapshot to database"""
        try:
            balance = self.exchange.get_balance('USDT')

            # Calculate total P&L
            trades = self.db_session.query(Trade).filter(Trade.status == 'closed').all()
            total_profit_loss = sum(t.profit_loss for t in trades)
            initial_balance = self.config['trading']['initial_balance']
            total_profit_loss_percent = (total_profit_loss / initial_balance) * 100 if initial_balance > 0 else 0

            # Count winning/losing trades
            winning_trades = sum(1 for t in trades if t.profit_loss > 0)
            losing_trades = sum(1 for t in trades if t.profit_loss < 0)

            # Calculate positions value
            positions_value = sum(
                pos['amount'] * pos.get('current_price', pos['entry_price'])
                for pos in self.risk_manager.get_open_positions()
            )

            balance_snapshot = Balance(
                total_balance=balance + positions_value,
                available_balance=balance,
                in_positions=positions_value,
                total_profit_loss=total_profit_loss,
                total_profit_loss_percent=total_profit_loss_percent,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades
            )

            self.db_session.add(balance_snapshot)
            self.db_session.commit()

        except Exception as e:
            logger.error(f"Error saving balance snapshot: {e}")
            # Rollback en cas d'erreur pour éviter session bloquée
            try:
                self.db_session.rollback()
            except:
                pass

    def get_status(self) -> Dict:
        """Get current bot status"""
        balance = self.exchange.get_balance('USDT')
        positions = self.risk_manager.get_open_positions()

        return {
            'running': self.running,
            'paused': self.paused,
            'balance': balance,
            'positions': positions,
            'risk_metrics': self.risk_manager.get_risk_metrics()
        }
