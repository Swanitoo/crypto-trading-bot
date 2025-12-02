from openai import OpenAI
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize OpenAI Market Analyzer

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"🤖 Market Analyzer initialized with model: {model}")

    def analyze_market(self,
                      pair: str,
                      ohlcv_data: List[Dict],
                      technical_indicators: Dict,
                      order_book: Optional[Dict] = None) -> Dict:
        """
        Analyze market data and provide trading recommendation

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            ohlcv_data: Recent candlestick data
            technical_indicators: Calculated technical indicators
            order_book: Current order book data

        Returns:
            Dict with recommendation, confidence, and reasoning
        """
        try:
            # Prepare market data summary
            latest_candle = ohlcv_data[-1] if ohlcv_data else {}
            recent_prices = [c['close'] for c in ohlcv_data[-20:]] if len(ohlcv_data) >= 20 else []

            market_summary = {
                'pair': pair,
                'current_price': latest_candle.get('close', 0),
                'price_change_24h': technical_indicators.get('price_change_24h', 0),
                'volume': latest_candle.get('volume', 0),
                'recent_prices': recent_prices,
                'indicators': technical_indicators
            }

            # Create prompt for GPT
            prompt = self._create_analysis_prompt(market_summary, order_book)

            # Get GPT analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un expert en analyse de trading de cryptomonnaies.
                        Ton rôle est d'analyser les données du marché et de fournir des recommandations de trading claires.
                        Tu dois considérer :
                        - Les indicateurs techniques (RSI, MACD, EMA)
                        - Les tendances de prix et le momentum
                        - Le sentiment du marché
                        - Les ratios risque/récompense

                        Réponds TOUJOURS en JSON avec :
                        {
                            "recommendation": "buy" | "sell" | "hold",
                            "confidence": 0-100,
                            "reasoning": "explication brève EN FRANÇAIS",
                            "entry_price": prix d'entrée suggéré,
                            "take_profit": prix de prise de profit suggéré,
                            "stop_loss": prix de stop-loss suggéré,
                            "risk_level": "low" | "medium" | "high"
                        }

                        Sois conservateur et privilégie la préservation du capital.
                        IMPORTANT : Le "reasoning" doit être en FRANÇAIS et clair."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # Parse response
            analysis = json.loads(response.choices[0].message.content)

            logger.info(f"🤖 AI Analysis for {pair}: {analysis['recommendation'].upper()} "
                       f"(Confidence: {analysis['confidence']}%)")
            logger.info(f"   Reasoning: {analysis['reasoning']}")

            return {
                'recommendation': analysis.get('recommendation', 'hold'),
                'confidence': analysis.get('confidence', 0),
                'reasoning': analysis.get('reasoning', ''),
                'entry_price': analysis.get('entry_price', market_summary['current_price']),
                'take_profit': analysis.get('take_profit', 0),
                'stop_loss': analysis.get('stop_loss', 0),
                'risk_level': analysis.get('risk_level', 'medium'),
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error in AI market analysis: {e}")
            return {
                'recommendation': 'hold',
                'confidence': 0,
                'reasoning': f'Analysis failed: {str(e)}',
                'entry_price': 0,
                'take_profit': 0,
                'stop_loss': 0,
                'risk_level': 'high',
                'timestamp': datetime.now()
            }

    def _create_analysis_prompt(self, market_summary: Dict, order_book: Optional[Dict]) -> str:
        """Create a detailed prompt for GPT analysis"""

        prompt = f"""Analyse ces données du marché crypto et fournis une recommandation de trading :

PAIRE: {market_summary['pair']}
PRIX ACTUEL: ${market_summary['current_price']:.2f}
VARIATION 24H: {market_summary['price_change_24h']:.2f}%
VOLUME: {market_summary['volume']:.2f}

INDICATEURS TECHNIQUES:
"""

        indicators = market_summary['indicators']
        if 'rsi' in indicators:
            prompt += f"- RSI: {indicators['rsi']:.2f} "
            if indicators['rsi'] < 30:
                prompt += "(SURVENDU)\n"
            elif indicators['rsi'] > 70:
                prompt += "(SURACHETÉ)\n"
            else:
                prompt += "(NEUTRE)\n"

        if 'macd' in indicators:
            prompt += f"- MACD: {indicators['macd']:.4f}\n"
            prompt += f"- MACD Signal: {indicators['macd_signal']:.4f}\n"
            prompt += f"- MACD Histogramme: {indicators['macd_histogram']:.4f}\n"

        if 'ema_20' in indicators and 'ema_50' in indicators:
            prompt += f"- EMA 20: ${indicators['ema_20']:.2f}\n"
            prompt += f"- EMA 50: ${indicators['ema_50']:.2f}\n"
            if indicators['ema_20'] > indicators['ema_50']:
                prompt += "  (CROISEMENT HAUSSIER)\n"
            else:
                prompt += "  (CROISEMENT BAISSIER)\n"

        if 'trend' in indicators:
            trend_fr = {
                'strong_uptrend': 'forte hausse',
                'uptrend': 'hausse',
                'sideways': 'latéral',
                'downtrend': 'baisse',
                'strong_downtrend': 'forte baisse',
                'unknown': 'inconnu'
            }.get(indicators['trend'], indicators['trend'])
            prompt += f"- TENDANCE: {trend_fr}\n"

        if 'volatility' in indicators:
            prompt += f"- VOLATILITÉ: {indicators['volatility']:.2f}%\n"

        # Add recent price action
        if market_summary['recent_prices']:
            prices = market_summary['recent_prices']
            price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
            prompt += f"\nACTION DU PRIX RÉCENTE (20 dernières périodes):"
            prompt += f"\n- Mouvement de prix: {price_change:+.2f}%"
            prompt += f"\n- Plus haut: ${max(prices):.2f}"
            prompt += f"\n- Plus bas: ${min(prices):.2f}"

        # Add order book info if available
        if order_book:
            prompt += f"\n\nORDRE DE MARCHÉ:"
            prompt += f"\n- Meilleure offre: ${order_book['bids'][0][0]:.2f}" if order_book.get('bids') else ""
            prompt += f"\n- Meilleure demande: ${order_book['asks'][0][0]:.2f}" if order_book.get('asks') else ""

        prompt += """\n\nSur la base de ces données, fournis une recommandation de trading.
Considère que nous faisons de petits trades avec des objectifs de profit serrés (5-10%).
Concentre-toi sur des configurations à haute probabilité avec de bons ratios risque/récompense.
RÉPONDS EN FRANÇAIS dans le champ "reasoning"."""

        return prompt

    def get_market_sentiment(self, pair: str, news_headlines: Optional[List[str]] = None) -> Dict:
        """
        Analyze market sentiment (optional advanced feature)

        Args:
            pair: Trading pair
            news_headlines: Optional news headlines to analyze

        Returns:
            Sentiment analysis
        """
        try:
            if not news_headlines:
                return {'sentiment': 'neutral', 'score': 50}

            prompt = f"""Analyze the sentiment for {pair} based on these news headlines:

{chr(10).join(f'- {headline}' for headline in news_headlines)}

Rate the overall sentiment from 0 (very bearish) to 100 (very bullish)."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a crypto market sentiment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            sentiment_text = response.choices[0].message.content.lower()

            # Simple sentiment parsing
            if 'bullish' in sentiment_text or 'positive' in sentiment_text:
                sentiment = 'bullish'
                score = 70
            elif 'bearish' in sentiment_text or 'negative' in sentiment_text:
                sentiment = 'bearish'
                score = 30
            else:
                sentiment = 'neutral'
                score = 50

            return {
                'sentiment': sentiment,
                'score': score,
                'analysis': sentiment_text
            }

        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'sentiment': 'neutral', 'score': 50, 'analysis': str(e)}
