from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import logging
from datetime import datetime, timedelta
from functools import wraps

from ..database.models import init_db, get_db_session, Trade, Balance, AIAnalysis

logger = logging.getLogger(__name__)

# Global bot instance (will be set from main.py)
trading_bot = None

def create_app(config):
    """Create Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('flask_secret_key', 'dev-secret-key')

    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize database (creates tables if needed)
    init_db()

    @app.route('/')
    def index():
        """Dashboard homepage"""
        return render_template('dashboard.html')

    @app.route('/api/status')
    def get_status():
        """Get bot status"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        status = trading_bot.get_status()
        return jsonify(status)

    @app.route('/api/balance')
    def get_balance():
        """Get current balance and P&L"""
        db = get_db_session()
        try:
            latest_balance = db.query(Balance).order_by(
                Balance.timestamp.desc()
            ).first()

            if not latest_balance:
                return jsonify({
                    'total_balance': 0,
                    'available_balance': 0,
                    'in_positions': 0,
                    'total_profit_loss': 0,
                    'total_profit_loss_percent': 0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0
                })

            return jsonify(latest_balance.to_dict())
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/trades')
    def get_trades():
        """Get recent trades"""
        db = get_db_session()
        try:
            limit = request.args.get('limit', 20, type=int)
            trades = db.query(Trade).order_by(
                Trade.timestamp.desc()
            ).limit(limit).all()

            return jsonify([trade.to_dict() for trade in trades])
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/positions')
    def get_positions():
        """Get open positions"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        positions = trading_bot.risk_manager.get_open_positions()

        # Update positions with REAL-TIME prices
        for pos in positions:
            try:
                ticker = trading_bot.exchange.get_ticker(pos['pair'])
                if ticker:
                    current_price = ticker['price']
                    pos['current_price'] = current_price

                    # Recalculate P&L with real-time price
                    entry_price = pos['entry_price']
                    amount = pos['amount']
                    pos['profit_loss'] = (current_price - entry_price) * amount
                    pos['profit_loss_percent'] = ((current_price / entry_price) - 1) * 100
            except Exception as e:
                logger.warning(f"Could not update price for {pos['pair']}: {e}")

        return jsonify(positions)

    @app.route('/api/ai_analysis')
    def get_ai_analysis():
        """Get recent AI analysis"""
        db = get_db_session()
        try:
            limit = request.args.get('limit', 10, type=int)
            analyses = db.query(AIAnalysis).order_by(
                AIAnalysis.timestamp.desc()
            ).limit(limit).all()

            return jsonify([analysis.to_dict() for analysis in analyses])
        except Exception as e:
            logger.error(f"Error fetching AI analysis: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/performance')
    def get_performance():
        """Get performance metrics"""
        db = get_db_session()
        try:
            # Get balance history for the last 24 hours
            since = datetime.now() - timedelta(hours=24)
            balances = db.query(Balance).filter(
                Balance.timestamp >= since
            ).order_by(Balance.timestamp.asc()).all()

            # Get trades history
            trades = db.query(Trade).filter(
                Trade.timestamp >= since,
                Trade.status == 'closed'
            ).all()

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.profit_loss > 0)
            losing_trades = sum(1 for t in trades if t.profit_loss < 0)
            total_profit = sum(t.profit_loss for t in trades if t.profit_loss > 0)
            total_loss = sum(abs(t.profit_loss) for t in trades if t.profit_loss < 0)

            return jsonify({
                'balance_history': [
                    {
                        'timestamp': b.timestamp.isoformat(),
                        'balance': b.total_balance
                    }
                    for b in balances
                ],
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'profit_factor': (total_profit / total_loss) if total_loss > 0 else 0
            })
        except Exception as e:
            logger.error(f"Error fetching performance: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    # Cache pour market overview
    market_overview_cache = {'data': None, 'timestamp': 0}
    CACHE_DURATION = 10  # 10 secondes

    @app.route('/api/market_overview')
    def get_market_overview():
        """Get market overview for all trading pairs"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        try:
            import time
            current_time = time.time()

            # Utiliser le cache si valide
            if market_overview_cache['data'] and (current_time - market_overview_cache['timestamp'] < CACHE_DURATION):
                return jsonify(market_overview_cache['data'])

            pairs = trading_bot.pairs
            overview = []

            for pair in pairs:
                try:
                    ticker = trading_bot.exchange.get_ticker(pair)
                    if ticker:
                        overview.append({
                            'pair': pair,
                            'price': ticker['price'],
                            'change_24h': ticker.get('change_24h', 0)
                        })
                except Exception as e:
                    logger.warning(f"Could not fetch ticker for {pair}: {e}")
                    continue

            # Mettre en cache
            market_overview_cache['data'] = overview
            market_overview_cache['timestamp'] = current_time

            return jsonify(overview)
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/market/<pair>')
    def get_market_data(pair):
        """Get market data for a pair"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        try:
            ticker = trading_bot.exchange.get_ticker(pair)
            ohlcv = trading_bot.exchange.get_ohlcv(pair, timeframe='1h', limit=24)

            return jsonify({
                'ticker': ticker,
                'ohlcv': [
                    {
                        'timestamp': candle['timestamp'].isoformat(),
                        'open': candle['open'],
                        'high': candle['high'],
                        'low': candle['low'],
                        'close': candle['close'],
                        'volume': candle['volume']
                    }
                    for candle in ohlcv
                ] if ohlcv else []
            })
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/bot/start', methods=['POST'])
    def start_bot():
        """Start the trading bot"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        if trading_bot.running:
            return jsonify({'message': 'Bot already running'}), 200

        # Start bot in a separate thread
        thread = threading.Thread(target=trading_bot.start)
        thread.daemon = True
        thread.start()

        return jsonify({'message': 'Bot started'})

    @app.route('/api/bot/stop', methods=['POST'])
    def stop_bot():
        """Stop the trading bot"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        trading_bot.stop()
        return jsonify({'message': 'Bot stopped'})

    @app.route('/api/bot/pause', methods=['POST'])
    def pause_bot():
        """Pause the trading bot"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        trading_bot.pause()
        return jsonify({'message': 'Bot paused'})

    @app.route('/api/bot/resume', methods=['POST'])
    def resume_bot():
        """Resume the trading bot"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        trading_bot.resume()
        return jsonify({'message': 'Bot resumed'})

    @app.route('/api/pair_chart/<pair>')
    def get_pair_chart(pair):
        """Get chart data for a specific pair with entry/exit points"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        db = get_db_session()
        try:
            # Replace URL format (BTC-USDT) back to exchange format (BTC/USDT)
            pair = pair.replace('-', '/')

            # Get OHLCV data (last 50 candles on 1h timeframe) - réduit pour performance
            ohlcv = trading_bot.exchange.get_ohlcv(pair, timeframe='1h', limit=50)
            if not ohlcv:
                return jsonify({'error': 'Could not fetch OHLCV data'}), 500

            # Get all trades for this pair (both open and closed)
            trades = db.query(Trade).filter(
                Trade.pair == pair
            ).order_by(Trade.timestamp.asc()).all()

            # Get current position if exists
            position = trading_bot.risk_manager.get_position(pair)

            # Format trades with entry/exit info
            trade_markers = []
            for trade in trades:
                if trade.side == 'buy':
                    trade_markers.append({
                        'type': 'entry',
                        'timestamp': trade.timestamp.isoformat(),
                        'price': trade.price,
                        'amount': trade.amount,
                        'status': trade.status
                    })
                elif trade.side == 'sell':
                    trade_markers.append({
                        'type': 'exit',
                        'timestamp': trade.timestamp.isoformat(),
                        'price': trade.price,
                        'amount': trade.amount,
                        'profit_loss': trade.profit_loss,
                        'profit_loss_percent': trade.profit_loss_percent
                    })

            # Format OHLCV
            candles = [
                {
                    'timestamp': candle['timestamp'].isoformat(),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle['volume']
                }
                for candle in ohlcv
            ]

            return jsonify({
                'pair': pair,
                'candles': candles,
                'trades': trade_markers,
                'position': position
            })

        except Exception as e:
            logger.error(f"Error fetching pair chart data: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/api/live_pnl')
    def get_live_pnl():
        """Get live P&L for all open positions"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        try:
            positions = trading_bot.risk_manager.get_open_positions()

            total_pnl = 0
            total_pnl_percent = 0
            position_count = len(positions)

            positions_data = []
            for pos in positions:
                # Fetch REAL-TIME price from exchange
                pair = pos['pair']
                try:
                    ticker = trading_bot.exchange.get_ticker(pair)
                    current_price = ticker['price'] if ticker else pos.get('current_price', pos['entry_price'])

                    # Recalculate P&L with real-time price
                    entry_price = pos['entry_price']
                    amount = pos['amount']
                    profit_loss = (current_price - entry_price) * amount
                    profit_loss_percent = ((current_price / entry_price) - 1) * 100

                except Exception as e:
                    logger.warning(f"Could not fetch real-time price for {pair}: {e}")
                    current_price = pos.get('current_price', pos['entry_price'])
                    profit_loss = pos['profit_loss']
                    profit_loss_percent = pos['profit_loss_percent']

                total_pnl += profit_loss
                positions_data.append({
                    'pair': pair,
                    'entry_price': pos['entry_price'],
                    'current_price': current_price,
                    'amount': amount,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'stop_loss': pos.get('stop_loss'),
                    'take_profit': pos.get('take_profit')
                })

            # Calculate average P&L percent
            if position_count > 0:
                total_pnl_percent = sum(p['profit_loss_percent'] for p in positions_data) / position_count

            return jsonify({
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'position_count': position_count,
                'positions': positions_data
            })

        except Exception as e:
            logger.error(f"Error fetching live P&L: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/config/ai-interval', methods=['GET'])
    def get_ai_interval():
        """Get current AI analysis interval"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        try:
            interval = trading_bot.ai_analysis_interval
            return jsonify({'interval': interval})
        except Exception as e:
            logger.error(f"Error getting AI interval: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/config/ai-interval', methods=['POST'])
    def update_ai_interval():
        """Update AI analysis interval in real-time"""
        if not trading_bot:
            return jsonify({'error': 'Bot not initialized'}), 500

        try:
            data = request.get_json()
            interval = int(data.get('interval', 600))

            # Validate interval (1 min to 1 hour)
            if interval < 60 or interval > 3600:
                return jsonify({'error': 'Interval must be between 60 and 3600 seconds'}), 400

            # Update bot's AI analysis interval
            trading_bot.ai_analysis_interval = interval
            logger.info(f"AI analysis interval updated to {interval} seconds")

            return jsonify({
                'success': True,
                'interval': interval,
                'message': f'AI analysis interval updated to {interval}s'
            })

        except Exception as e:
            logger.error(f"Error updating AI interval: {e}")
            return jsonify({'error': str(e)}), 500

    return app, socketio

def set_trading_bot(bot):
    """Set the global trading bot instance"""
    global trading_bot
    trading_bot = bot
