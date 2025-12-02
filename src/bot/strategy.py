import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from typing import Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MarketContext(Enum):
    """Market context for adaptive trading strategy"""
    CRASH_RECOVERY = "crash_recovery"      # RSI < 25, forte baisse → BUY THE DIP agressif
    DIP_OPPORTUNITY = "dip_opportunity"    # RSI 25-35 → BUY bounce
    STRONG_MOMENTUM = "strong_momentum"    # RSI > 60, hausse forte → BUY momentum
    BREAKOUT = "breakout"                  # Cassure résistance → BUY
    CONSOLIDATION = "consolidation"        # Sideways, RSI 40-60 → WAIT
    DOWNTREND = "downtrend"                # Baisse continue → SKIP
    REVERSAL_SETUP = "reversal_setup"      # Début de retournement → BUY prudent

class TradingStrategy:
    """Technical analysis and trading strategy engine"""

    def __init__(self, config: Dict):
        self.config = config
        self.indicators = config.get('indicators', ['RSI', 'MACD', 'EMA'])
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)

    def calculate_indicators(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Calculate technical indicators from OHLCV data

        Args:
            ohlcv_data: List of OHLCV candles

        Returns:
            Dict containing calculated indicators
        """
        if len(ohlcv_data) < 50:
            logger.warning("Not enough data for indicator calculation")
            return {}

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(ohlcv_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

            indicators = {}

            # Calculate RSI
            if 'RSI' in self.indicators:
                rsi = RSIIndicator(close=df['close'], window=14)
                indicators['rsi'] = float(rsi.rsi().iloc[-1])
                indicators['rsi_signal'] = self._get_rsi_signal(indicators['rsi'])

            # Calculate MACD
            if 'MACD' in self.indicators:
                macd = MACD(close=df['close'])
                indicators['macd'] = float(macd.macd().iloc[-1])
                indicators['macd_signal'] = float(macd.macd_signal().iloc[-1])
                indicators['macd_histogram'] = float(macd.macd_diff().iloc[-1])
                indicators['macd_trend'] = 'bullish' if indicators['macd_histogram'] > 0 else 'bearish'

            # Calculate EMAs
            if 'EMA' in self.indicators:
                ema_20 = EMAIndicator(close=df['close'], window=20)
                ema_50 = EMAIndicator(close=df['close'], window=50)
                indicators['ema_20'] = float(ema_20.ema_indicator().iloc[-1])
                indicators['ema_50'] = float(ema_50.ema_indicator().iloc[-1])
                indicators['ema_crossover'] = 'bullish' if indicators['ema_20'] > indicators['ema_50'] else 'bearish'

            # Calculate Bollinger Bands
            bb = BollingerBands(close=df['close'], window=20, window_dev=2)
            indicators['bb_upper'] = float(bb.bollinger_hband().iloc[-1])
            indicators['bb_middle'] = float(bb.bollinger_mavg().iloc[-1])
            indicators['bb_lower'] = float(bb.bollinger_lband().iloc[-1])

            # Current price info
            current_price = float(df['close'].iloc[-1])
            indicators['current_price'] = current_price
            indicators['price_change_24h'] = ((current_price - float(df['close'].iloc[0])) / float(df['close'].iloc[0])) * 100

            # Trend detection
            indicators['trend'] = self._detect_trend(df)

            # Volatility
            indicators['volatility'] = float(df['close'].pct_change().std() * 100)

            # Support and Resistance
            indicators['support'] = float(df['low'].tail(20).min())
            indicators['resistance'] = float(df['high'].tail(20).max())

            logger.info(f"📊 Indicators calculated: RSI={indicators.get('rsi', 0):.2f}, "
                       f"Trend={indicators.get('trend', 'unknown')}")

            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def _get_rsi_signal(self, rsi: float) -> str:
        """Get trading signal from RSI"""
        if rsi < self.rsi_oversold:
            return 'oversold'
        elif rsi > self.rsi_overbought:
            return 'overbought'
        else:
            return 'neutral'

    def _detect_trend(self, df: pd.DataFrame) -> str:
        """Detect overall trend from price data"""
        try:
            # Calculate simple moving averages
            sma_short = df['close'].tail(10).mean()
            sma_long = df['close'].tail(30).mean()

            # Calculate price momentum
            price_change = ((df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]) * 100

            if sma_short > sma_long and price_change > 2:
                return 'strong_uptrend'
            elif sma_short > sma_long and price_change > 0:
                return 'uptrend'
            elif sma_short < sma_long and price_change < -2:
                return 'strong_downtrend'
            elif sma_short < sma_long and price_change < 0:
                return 'downtrend'
            else:
                return 'sideways'
        except:
            return 'unknown'

    def detect_market_context(self, indicators: Dict) -> Tuple[MarketContext, Dict]:
        """
        Détecte le contexte de marché pour adapter la stratégie

        Returns:
            (MarketContext, adaptive_params) avec TP/SL adaptatifs
        """
        rsi = indicators.get('rsi', 50)
        trend = indicators.get('trend', 'unknown')
        macd_hist = indicators.get('macd_histogram', 0)
        price_change_24h = indicators.get('price_change_24h', 0)
        current_price = indicators.get('current_price', 0)
        resistance = indicators.get('resistance', 0)
        volatility = indicators.get('volatility', 0)

        # Paramètres par défaut
        params = {
            'take_profit_percent': 3.0,
            'stop_loss_percent': 2.0,
            'confidence_boost': 0,
            'max_positions': 3
        }

        # 1. CRASH RECOVERY - RSI < 25, forte baisse
        if rsi < 25 and price_change_24h < -5:
            logger.info(f"🚨 CRASH RECOVERY detected! RSI={rsi:.1f}, Change={price_change_24h:.1f}%")
            params.update({
                'take_profit_percent': 2.0,   # TP rapide
                'stop_loss_percent': 1.0,     # SL serré
                'confidence_boost': 25,       # Boost confiance pour entrer
                'max_positions': 5            # Plus de positions possibles
            })
            return MarketContext.CRASH_RECOVERY, params

        # 2. DIP OPPORTUNITY - RSI 25-35 (oversold mais pas extrême)
        if 25 <= rsi < 35:
            logger.info(f"💎 DIP OPPORTUNITY detected! RSI={rsi:.1f}")
            params.update({
                'take_profit_percent': 2.5,
                'stop_loss_percent': 1.5,
                'confidence_boost': 15,
                'max_positions': 4
            })
            return MarketContext.DIP_OPPORTUNITY, params

        # 3. STRONG MOMENTUM - RSI > 60, hausse forte, MACD positif
        if rsi > 60 and price_change_24h > 3 and macd_hist > 0:
            logger.info(f"🚀 STRONG MOMENTUM detected! RSI={rsi:.1f}, Change={price_change_24h:.1f}%")
            params.update({
                'take_profit_percent': 4.0,   # TP plus haut (momentum)
                'stop_loss_percent': 2.5,
                'confidence_boost': 20,
                'max_positions': 4
            })
            return MarketContext.STRONG_MOMENTUM, params

        # 4. BREAKOUT - Prix proche de la résistance + momentum
        if resistance > 0 and current_price >= resistance * 0.98 and macd_hist > 0:
            logger.info(f"💥 BREAKOUT detected! Price near resistance")
            params.update({
                'take_profit_percent': 3.5,
                'stop_loss_percent': 1.5,
                'confidence_boost': 15,
                'max_positions': 3
            })
            return MarketContext.BREAKOUT, params

        # 5. REVERSAL SETUP - RSI commence à remonter après oversold
        if 35 <= rsi < 45 and trend in ['sideways', 'downtrend'] and macd_hist > 0:
            logger.info(f"🔄 REVERSAL SETUP detected! RSI={rsi:.1f}")
            params.update({
                'take_profit_percent': 3.0,
                'stop_loss_percent': 2.0,
                'confidence_boost': 10,
                'max_positions': 3
            })
            return MarketContext.REVERSAL_SETUP, params

        # 6. DOWNTREND - Éviter de trader
        if trend in ['downtrend', 'strong_downtrend'] and rsi < 50 and macd_hist < 0:
            logger.info(f"📉 DOWNTREND detected - staying cautious")
            params.update({
                'take_profit_percent': 3.0,
                'stop_loss_percent': 2.0,
                'confidence_boost': -20,  # Réduit confiance
                'max_positions': 2
            })
            return MarketContext.DOWNTREND, params

        # 7. CONSOLIDATION - Par défaut (sideways)
        logger.info(f"📊 CONSOLIDATION detected")
        return MarketContext.CONSOLIDATION, params

    def generate_signal(self, indicators: Dict, ai_analysis: Dict = None) -> Dict:
        """
        Generate trading signal based on indicators and AI analysis (ADAPTIVE)

        Args:
            indicators: Technical indicators
            ai_analysis: AI market analysis (optional)

        Returns:
            Dict with signal, confidence, reasoning, and adaptive params
        """
        # Détecter le contexte de marché
        market_context, adaptive_params = self.detect_market_context(indicators)

        signals = []
        confidence_scores = []
        reasons = []

        # Ajouter le contexte aux raisons
        reasons.append(f"Context: {market_context.value}")

        # RSI Signal - Plus agressif en contexte favorable
        if 'rsi' in indicators:
            rsi = indicators['rsi']

            # BUY THE DIP - agressif si RSI très bas
            if rsi < 25 and market_context in [MarketContext.CRASH_RECOVERY, MarketContext.DIP_OPPORTUNITY]:
                signals.append('buy')
                confidence_scores.append(80)  # Très confiant sur les dips
                reasons.append(f"RSI extreme oversold ({rsi:.1f}) - BUY THE DIP!")
            elif rsi < 35 and market_context == MarketContext.DIP_OPPORTUNITY:
                signals.append('buy')
                confidence_scores.append(70)
                reasons.append(f"RSI oversold ({rsi:.1f}) - DIP OPPORTUNITY")
            elif rsi < self.rsi_oversold:
                signals.append('buy')
                confidence_scores.append(65)
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > self.rsi_overbought:
                # Ne pas vendre si en strong momentum
                if market_context != MarketContext.STRONG_MOMENTUM:
                    signals.append('sell')
                    confidence_scores.append(60)
                    reasons.append(f"RSI overbought ({rsi:.1f})")

        # MACD Signal - Boost en momentum fort
        if 'macd_histogram' in indicators:
            macd_hist = indicators['macd_histogram']
            if macd_hist > 0 and indicators.get('macd_trend') == 'bullish':
                # Boost si strong momentum
                confidence = 75 if market_context == MarketContext.STRONG_MOMENTUM else 60
                signals.append('buy')
                confidence_scores.append(confidence)
                reasons.append("MACD bullish")
            elif macd_hist < 0 and indicators.get('macd_trend') == 'bearish':
                # Ne pas vendre en crash recovery (attendre bounce)
                if market_context not in [MarketContext.CRASH_RECOVERY, MarketContext.DIP_OPPORTUNITY]:
                    signals.append('sell')
                    confidence_scores.append(60)
                    reasons.append("MACD bearish")

        # EMA Crossover Signal
        if 'ema_crossover' in indicators:
            if indicators['ema_crossover'] == 'bullish':
                signals.append('buy')
                confidence_scores.append(50)
                reasons.append("EMA bullish crossover")
            elif indicators['ema_crossover'] == 'bearish':
                # Ne pas vendre en dip (attendre bounce)
                if market_context not in [MarketContext.CRASH_RECOVERY, MarketContext.DIP_OPPORTUNITY]:
                    signals.append('sell')
                    confidence_scores.append(50)
                    reasons.append("EMA bearish crossover")

        # Trend Signal - Agressif sur momentum
        if 'trend' in indicators:
            trend = indicators['trend']
            if trend in ['strong_uptrend', 'uptrend']:
                confidence = 60 if trend == 'strong_uptrend' else 40
                signals.append('buy')
                confidence_scores.append(confidence)
                reasons.append(f"Price in {trend}")
            elif trend in ['strong_downtrend'] and market_context == MarketContext.CRASH_RECOVERY:
                # En crash extrême, acheter quand même (contrarian)
                signals.append('buy')
                confidence_scores.append(50)
                reasons.append(f"CONTRARIAN: extreme downtrend = buy opportunity")
            elif trend in ['downtrend']:
                # Seulement si pas en recovery mode
                if market_context not in [MarketContext.CRASH_RECOVERY, MarketContext.DIP_OPPORTUNITY, MarketContext.REVERSAL_SETUP]:
                    signals.append('sell')
                    confidence_scores.append(40)
                    reasons.append(f"Price in {trend}")

        # Combine with AI analysis if available
        if ai_analysis and ai_analysis.get('confidence', 0) >= self.config.get('ai_confidence_threshold', 70):
            ai_signal = ai_analysis['recommendation']
            ai_confidence = ai_analysis['confidence']

            signals.append(ai_signal)
            confidence_scores.append(ai_confidence)
            reasons.append(f"AI: {ai_analysis.get('reasoning', 'N/A')}")

        # Aggregate signals
        if not signals:
            return {
                'action': 'hold',
                'confidence': 0,
                'reasoning': 'No clear signals',
                'adaptive_params': adaptive_params,
                'market_context': market_context.value
            }

        # Count votes
        buy_votes = signals.count('buy')
        sell_votes = signals.count('sell')
        hold_votes = signals.count('hold')

        # Determine final action
        if buy_votes > sell_votes and buy_votes > hold_votes:
            action = 'buy'
            confidence = np.mean([confidence_scores[i] for i, s in enumerate(signals) if s == 'buy'])
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            action = 'sell'
            confidence = np.mean([confidence_scores[i] for i, s in enumerate(signals) if s == 'sell'])
        else:
            action = 'hold'
            confidence = np.mean(confidence_scores) if confidence_scores else 0

        # Apply confidence boost from market context
        confidence = min(100, confidence + adaptive_params['confidence_boost'])

        logger.info(f"🎯 Signal: {action.upper()} | Confidence: {confidence:.1f}% (boost: +{adaptive_params['confidence_boost']}%)")

        return {
            'action': action,
            'confidence': float(confidence),
            'reasoning': ' | '.join(reasons),
            'adaptive_params': adaptive_params,
            'market_context': market_context.value,
            'votes': {
                'buy': buy_votes,
                'sell': sell_votes,
                'hold': hold_votes
            }
        }

    def calculate_position_size(self, balance: float, risk_percent: float = 2.0) -> float:
        """
        Calculate position size based on risk management

        Args:
            balance: Available balance
            risk_percent: Percentage of balance to risk per trade

        Returns:
            Position size in USDT
        """
        return balance * (risk_percent / 100)
