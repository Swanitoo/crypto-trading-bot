from typing import Dict, Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Position:
    """
    Position avec support DCA (Dollar Cost Averaging)
    Permet plusieurs entrées sur la même paire pour lisser le prix
    """
    def __init__(self, pair: str, side: str = 'long'):
        self.pair = pair
        self.side = side
        self.entries = []  # Liste des entrées [(price, amount, timestamp, fees)]
        self.exits = []    # Liste des sorties partielles
        self.status = 'open'
        self.highest_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.tp_percent = 3.0
        self.sl_percent = 2.0

        # Partial take profit levels (adaptatifs selon contexte)
        self.partial_tp_levels = []  # Liste de [(profit_percent, sell_percent)]
        self.completed_tp_levels = []  # Niveaux déjà exécutés

    def add_entry(self, price: float, amount: float, fees: float = 0.0):
        """Ajoute une entrée (accumulation DCA)"""
        entry = {
            'price': price,
            'amount': amount,
            'fees': fees,
            'timestamp': datetime.now(),
            'cost': price * amount + fees  # Coût total incluant frais
        }
        self.entries.append(entry)

        # Mettre à jour highest_price
        if price > self.highest_price:
            self.highest_price = price

        logger.info(f"   📥 Entry added: {amount:.8f} @ ${price:.2f} (fees: ${fees:.4f})")

    def add_exit(self, price: float, amount: float, fees: float = 0.0):
        """Ajoute une sortie partielle"""
        exit_entry = {
            'price': price,
            'amount': amount,
            'fees': fees,
            'timestamp': datetime.now(),
            'proceeds': price * amount - fees  # Montant reçu après frais
        }
        self.exits.append(exit_entry)
        logger.info(f"   📤 Partial exit: {amount:.8f} @ ${price:.2f} (fees: ${fees:.4f})")

    def get_average_entry_price(self) -> float:
        """Calcule le prix d'entrée moyen pondéré (AVEC FRAIS)"""
        if not self.entries:
            return 0.0

        total_cost = sum(e['cost'] for e in self.entries)
        total_amount = sum(e['amount'] for e in self.entries)

        if total_amount == 0:
            return 0.0

        return total_cost / total_amount  # Prix moyen incluant frais

    def get_total_amount(self) -> float:
        """Montant total accumulé"""
        return sum(e['amount'] for e in self.entries) - sum(e['amount'] for e in self.exits)

    def get_total_cost(self) -> float:
        """Coût total de toutes les entrées (incluant frais)"""
        return sum(e['cost'] for e in self.entries)

    def calculate_pnl(self, current_price: float, include_fees: bool = True) -> Tuple[float, float]:
        """
        Calcule le P&L réel (incluant frais de vente)
        Returns: (profit_loss_usd, profit_loss_percent)
        """
        total_amount = self.get_total_amount()
        if total_amount == 0:
            return 0.0, 0.0

        avg_entry = self.get_average_entry_price()  # Déjà avec frais d'achat

        # Valeur actuelle
        current_value = current_price * total_amount

        # Si on inclut les frais de vente (0.1%)
        if include_fees:
            sell_fees = current_value * 0.001  # 0.1% de frais
            current_value -= sell_fees

        # P&L
        total_cost = self.get_total_cost()
        profit_loss = current_value - total_cost
        profit_loss_percent = (profit_loss / total_cost) * 100 if total_cost > 0 else 0.0

        return profit_loss, profit_loss_percent

    def set_partial_tp_levels(self, levels: List[Tuple[float, float]]):
        """
        Définit les niveaux de partial take profit
        Args:
            levels: Liste de (profit_percent, sell_percent)
                    Ex: [(1.5, 40), (2.5, 40)] = vendre 40% à +1.5%, 40% à +2.5%
        """
        self.partial_tp_levels = sorted(levels, key=lambda x: x[0])  # Trier par profit%
        self.completed_tp_levels = []
        logger.info(f"   🎯 Partial TP levels: {self.partial_tp_levels}")

    def check_partial_tp(self, current_price: float) -> Optional[Tuple[float, float]]:
        """
        Vérifie si un niveau de partial TP est atteint
        Returns: (profit_percent, sell_percent) si un niveau est atteint, None sinon
        """
        if not self.partial_tp_levels:
            return None

        _, profit_percent = self.calculate_pnl(current_price, include_fees=True)

        for tp_level, sell_percent in self.partial_tp_levels:
            # Si niveau atteint ET pas encore exécuté
            if profit_percent >= tp_level and tp_level not in self.completed_tp_levels:
                return (tp_level, sell_percent)

        return None

class RiskManager:
    """Risk management system for trading bot with DCA support"""

    def __init__(self, config: Dict):
        self.config = config
        self.take_profit_percent = config.get('take_profit_percent', 5.0)
        self.stop_loss_percent = config.get('stop_loss_percent', 3.0)
        self.max_positions = config.get('max_positions', 2)
        self.max_daily_loss = config.get('max_daily_loss_percent', 10.0)
        self.use_trailing_stop = config.get('use_trailing_stop', True)
        self.trading_fees_percent = config.get('trading_fees_percent', 0.1)  # Binance: 0.1%
        self.enable_dca = config.get('enable_dca', True)  # DCA activé par défaut
        self.dca_threshold_percent = config.get('dca_threshold_percent', -2.0)  # Accumuler si -2%

        self.daily_losses = 0.0
        self.daily_trades = 0
        self.positions = {}  # Dict[str, Position]

    def can_open_position(self, balance: float, trade_amount: float, pair: str = None) -> tuple[bool, str]:
        """
        Check if we can open a new position OR accumulate on existing (DCA)

        Returns:
            (can_trade, reason)
        """
        # Si DCA activé et position existe, on peut toujours accumuler
        if self.enable_dca and pair and self.has_position(pair):
            position = self.positions[pair]
            # Vérifier si on peut accumuler (prix a baissé suffisamment)
            current_avg = position.get_average_entry_price()
            # On peut toujours accumuler tant qu'on a le budget
            if balance < trade_amount:
                return False, f"Insufficient balance for DCA ({balance:.2f} < {trade_amount:.2f})"
            return True, "DCA accumulation"

        # Check if we have enough positions
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"

        # Check if we have enough balance
        if balance < trade_amount:
            return False, f"Insufficient balance ({balance:.2f} < {trade_amount:.2f})"

        # Check daily loss limit
        if self.daily_losses >= self.max_daily_loss:
            return False, f"Daily loss limit reached ({self.daily_losses:.2f}%)"

        return True, "OK"

    def should_accumulate(self, pair: str, current_price: float) -> tuple[bool, str]:
        """
        Détermine si on doit accumuler (DCA) sur une position existante
        Returns: (should_accumulate, reason)
        """
        if not self.enable_dca or pair not in self.positions:
            return False, "DCA disabled or no position"

        position = self.positions[pair]
        avg_entry = position.get_average_entry_price()

        # Calculer le % de baisse depuis le prix moyen
        price_drop_percent = ((current_price - avg_entry) / avg_entry) * 100

        # Accumuler si baisse >= seuil DCA (ex: -2%)
        if price_drop_percent <= self.dca_threshold_percent:
            return True, f"Price dropped {price_drop_percent:.2f}% → DCA opportunity"

        return False, f"Price drop insufficient ({price_drop_percent:.2f}% > {self.dca_threshold_percent}%)"

    def open_position(self, pair: str, entry_price: float, amount: float,
                     side: str = 'long', custom_tp_percent: float = None,
                     custom_sl_percent: float = None, trade_amount_usd: float = 0) -> Dict:
        """
        Open a new position OR accumulate (DCA) on existing position

        Args:
            pair: Trading pair
            entry_price: Entry price
            amount: Crypto amount
            side: 'long' or 'short'
            custom_tp_percent: Custom take-profit percentage
            custom_sl_percent: Custom stop-loss percentage
            trade_amount_usd: Amount in USD (for fees calculation)

        Returns:
            Position dict
        """
        # Use custom or default TP/SL
        tp_percent = custom_tp_percent if custom_tp_percent is not None else self.take_profit_percent
        sl_percent = custom_sl_percent if custom_sl_percent is not None else self.stop_loss_percent

        # Calculate fees (0.1% of trade)
        buy_fees = trade_amount_usd * (self.trading_fees_percent / 100)

        # Si position existe déjà, accumuler (DCA)
        if pair in self.positions:
            position = self.positions[pair]
            old_avg = position.get_average_entry_price()
            position.add_entry(entry_price, amount, buy_fees)
            new_avg = position.get_average_entry_price()

            logger.info(f"🔄 DCA Accumulation on {pair}:")
            logger.info(f"   Old avg: ${old_avg:.2f} → New avg: ${new_avg:.2f}")
            logger.info(f"   Total amount: {position.get_total_amount():.8f}")

            # Recalculer SL/TP basés sur nouveau prix moyen
            if side == 'long':
                position.stop_loss = new_avg * (1 - sl_percent / 100)
                position.take_profit = new_avg * (1 + tp_percent / 100)

            position.tp_percent = tp_percent
            position.sl_percent = sl_percent

            return self._position_to_dict(position)

        # Créer nouvelle position
        position = Position(pair, side)
        position.add_entry(entry_price, amount, buy_fees)
        position.tp_percent = tp_percent
        position.sl_percent = sl_percent

        # Calculate stop-loss and take-profit prices
        if side == 'long':
            position.stop_loss = entry_price * (1 - sl_percent / 100)
            position.take_profit = entry_price * (1 + tp_percent / 100)
        else:  # short
            position.stop_loss = entry_price * (1 + sl_percent / 100)
            position.take_profit = entry_price * (1 - tp_percent / 100)

        position.highest_price = entry_price

        self.positions[pair] = position

        # Définir les niveaux de partial TP adaptatifs
        self._set_adaptive_partial_tp(position, tp_percent)

        logger.info(f"📈 Position opened: {pair} at ${entry_price:.2f}")
        logger.info(f"   Amount: {amount:.8f} (cost: ${trade_amount_usd:.2f} + fees: ${buy_fees:.4f})")
        logger.info(f"   Stop-Loss: ${position.stop_loss:.2f} (-{sl_percent}%)")
        logger.info(f"   Take-Profit: ${position.take_profit:.2f} (+{tp_percent}%)")

        return self._position_to_dict(position)

    def _set_adaptive_partial_tp(self, position: Position, final_tp_percent: float):
        """
        Définit les niveaux de partial TP adaptatifs selon le TP final

        Stratégie:
        - 1er niveau : ~50% du chemin vers TP final → vendre 40%
        - 2ème niveau : ~75% du chemin vers TP final → vendre 40%
        - Reste (20%) : conservé avec trailing stop jusqu'au TP final ou SL
        """
        # Calculer les niveaux intermédiaires
        level_1 = final_tp_percent * 0.5  # 50% du chemin
        level_2 = final_tp_percent * 0.75  # 75% du chemin

        # Plus agressif si TP bas (crash recovery), plus patient si TP haut (momentum)
        if final_tp_percent <= 2.0:
            # Crash recovery : sortir vite
            levels = [
                (level_1, 50),  # 50% au premier niveau
                (level_2, 40),  # 40% au second
            ]
        elif final_tp_percent >= 3.5:
            # Strong momentum : laisser courir
            levels = [
                (level_1, 30),  # 30% au premier niveau
                (level_2, 30),  # 30% au second
            ]
        else:
            # Standard : équilibré
            levels = [
                (level_1, 40),  # 40% au premier niveau
                (level_2, 40),  # 40% au second
            ]

        position.set_partial_tp_levels(levels)

    def partial_exit(self, pair: str, exit_price: float, sell_percent: float,
                     tp_level: float) -> Optional[Dict]:
        """
        Vente partielle d'une position (Partial Take Profit)

        Args:
            pair: Trading pair
            exit_price: Exit price
            sell_percent: Percentage of position to sell (0-100)
            tp_level: TP level that triggered this exit

        Returns:
            Dict with exit info (amount_to_sell, profit, etc.)
        """
        if pair not in self.positions:
            logger.warning(f"Cannot partial exit {pair}: position not found")
            return None

        position = self.positions[pair]
        current_amount = position.get_total_amount()

        if current_amount <= 0:
            logger.warning(f"Cannot partial exit {pair}: no amount left")
            return None

        # Calculer le montant à vendre
        amount_to_sell = current_amount * (sell_percent / 100)

        # Calculer les frais de vente (0.1%)
        sale_value = amount_to_sell * exit_price
        sell_fees = sale_value * (self.trading_fees_percent / 100)

        # Enregistrer la sortie partielle
        position.add_exit(exit_price, amount_to_sell, sell_fees)

        # Marquer ce niveau TP comme complété
        position.completed_tp_levels.append(tp_level)

        # Calculer le profit de cette sortie partielle
        avg_entry = position.get_average_entry_price()
        partial_profit = (exit_price - avg_entry) * amount_to_sell - sell_fees
        partial_profit_percent = ((exit_price - avg_entry) / avg_entry) * 100

        # Remaining amount
        remaining_amount = position.get_total_amount()

        pnl_symbol = "🟢" if partial_profit > 0 else "🔴"
        logger.info(f"{pnl_symbol} Partial exit: {pair}")
        logger.info(f"   Sold: {amount_to_sell:.8f} ({sell_percent}%) @ ${exit_price:.2f}")
        logger.info(f"   Partial P&L: ${partial_profit:.2f} ({partial_profit_percent:+.2f}%)")
        logger.info(f"   Remaining: {remaining_amount:.8f} ({100-sell_percent}%)")
        logger.info(f"   TP Level: +{tp_level}%")

        return {
            'pair': pair,
            'amount_to_sell': amount_to_sell,
            'exit_price': exit_price,
            'sell_percent': sell_percent,
            'tp_level': tp_level,
            'partial_profit': partial_profit,
            'partial_profit_percent': partial_profit_percent,
            'remaining_amount': remaining_amount,
            'sell_fees': sell_fees
        }

    def _position_to_dict(self, position: Position) -> Dict:
        """Convert Position object to dict for compatibility"""
        return {
            'pair': position.pair,
            'side': position.side,
            'entry_price': position.get_average_entry_price(),
            'amount': position.get_total_amount(),
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit,
            'highest_price': position.highest_price,
            'tp_percent': position.tp_percent,
            'sl_percent': position.sl_percent,
            'status': position.status,
            'profit_loss': 0.0,
            'profit_loss_percent': 0.0,
            'entries_count': len(position.entries)
        }

    def update_position(self, pair: str, current_price: float) -> Optional[Dict]:
        """
        Update position with current price and REAL P&L (including fees)

        Args:
            pair: Trading pair
            current_price: Current market price

        Returns:
            Updated position dict or None
        """
        if pair not in self.positions:
            return None

        position = self.positions[pair]

        # Calculate REAL P&L (incluant frais de vente)
        profit_loss, profit_loss_percent = position.calculate_pnl(current_price, include_fees=True)

        # Update dict
        pos_dict = self._position_to_dict(position)
        pos_dict['current_price'] = current_price
        pos_dict['profit_loss'] = profit_loss
        pos_dict['profit_loss_percent'] = profit_loss_percent

        # Vérifier si un niveau de partial TP est atteint
        partial_tp_info = position.check_partial_tp(current_price)
        if partial_tp_info:
            tp_level, sell_percent = partial_tp_info
            pos_dict['partial_tp_triggered'] = True
            pos_dict['partial_tp_level'] = tp_level
            pos_dict['partial_tp_sell_percent'] = sell_percent
            logger.info(f"🎯 Partial TP triggered! Level: +{tp_level}% → Sell {sell_percent}%")
        else:
            pos_dict['partial_tp_triggered'] = False

        # TRAILING STOP AGRESSIF: Ajuster le Stop Loss si le prix monte
        if self.use_trailing_stop and position.side == 'long':
            # Si nouveau plus haut
            if current_price > position.highest_price:
                old_stop_loss = position.stop_loss
                position.highest_price = current_price

                # OPTIMISATION AGRESSIVE: Serrer le trailing stop selon le profit
                # Plus on est en profit, plus on sécurise (SL plus serré)
                sl_percent = position.sl_percent

                if profit_loss_percent >= 2.5:
                    # Profit > 2.5% : SL très serré (0.3%) - sécuriser les gains !
                    trailing_sl_percent = 0.3
                    logger.info(f"🔒 Profit élevé (+{profit_loss_percent:.2f}%) - SL ultra-serré activé!")
                elif profit_loss_percent >= 1.5:
                    # Profit 1.5-2.5% : SL serré (0.5%)
                    trailing_sl_percent = 0.5
                elif profit_loss_percent >= 0.8:
                    # Profit 0.8-1.5% : SL modéré (0.75%)
                    trailing_sl_percent = 0.75
                else:
                    # Profit < 0.8% : SL normal
                    trailing_sl_percent = sl_percent

                # Calculer nouveau stop loss basé sur le plus haut
                new_stop_loss = current_price * (1 - trailing_sl_percent / 100)

                # Le stop loss ne descend JAMAIS, seulement monte
                if new_stop_loss > old_stop_loss:
                    position.stop_loss = new_stop_loss
                    pos_dict['stop_loss'] = new_stop_loss
                    logger.info(f"📈 Trailing Stop ajusté pour {pair}: ${old_stop_loss:.2f} → ${new_stop_loss:.2f} (-{trailing_sl_percent}%)")
                    logger.info(f"   Prix actuel: ${current_price:.2f}, P&L RÉEL: +{profit_loss_percent:.2f}% (après frais)")

        return pos_dict

    def should_close_position(self, pair: str, current_price: float) -> tuple[bool, str]:
        """
        Check if position should be closed based on stop-loss or take-profit

        Args:
            pair: Trading pair
            current_price: Current market price

        Returns:
            (should_close, reason)
        """
        if pair not in self.positions:
            return False, "Position not found"

        position = self.positions[pair]

        # Check stop-loss
        if position.side == 'long':
            if current_price <= position.stop_loss:
                return True, f"Stop-loss triggered at ${current_price:.2f}"

            # Check take-profit
            if current_price >= position.take_profit:
                return True, f"Take-profit triggered at ${current_price:.2f}"
        else:  # short
            if current_price >= position.stop_loss:
                return True, f"Stop-loss triggered at ${current_price:.2f}"

            if current_price <= position.take_profit:
                return True, f"Take-profit triggered at ${current_price:.2f}"

        return False, "Position within range"

    def close_position(self, pair: str, exit_price: float, reason: str = "") -> Optional[Dict]:
        """
        Close a position and update statistics

        Args:
            pair: Trading pair
            exit_price: Exit price
            reason: Reason for closing

        Returns:
            Closed position dict
        """
        if pair not in self.positions:
            logger.warning(f"Cannot close position {pair}: not found")
            return None

        position = self.positions[pair]

        # Calculate final P&L using Position method (includes fees!)
        profit_loss, profit_loss_percent = position.calculate_pnl(exit_price, include_fees=True)

        # Create result dict
        result = self._position_to_dict(position)
        result['exit_price'] = exit_price
        result['exit_time'] = datetime.now()
        result['profit_loss'] = profit_loss
        result['profit_loss_percent'] = profit_loss_percent
        result['status'] = 'closed'
        result['close_reason'] = reason

        # Update daily statistics
        if profit_loss < 0:
            self.daily_losses += abs(profit_loss_percent)

        self.daily_trades += 1

        # Log the closed position
        pnl_symbol = "🟢" if profit_loss > 0 else "🔴"
        logger.info(f"{pnl_symbol} Position closed: {pair}")
        logger.info(f"   Avg Entry: ${position.get_average_entry_price():.2f} → Exit: ${exit_price:.2f}")
        logger.info(f"   Entries: {len(position.entries)} | Total Amount: {position.get_total_amount():.8f}")
        logger.info(f"   P&L RÉEL (après frais): ${profit_loss:.2f} ({profit_loss_percent:+.2f}%)")
        logger.info(f"   Reason: {reason}")

        # Remove from active positions
        del self.positions[pair]

        return result

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [self._position_to_dict(pos) for pos in self.positions.values()]

    def get_position(self, pair: str) -> Optional[Dict]:
        """Get specific position"""
        position = self.positions.get(pair)
        return self._position_to_dict(position) if position else None

    def has_position(self, pair: str) -> bool:
        """Check if we have an open position for a pair"""
        return pair in self.positions

    def reset_daily_stats(self):
        """Reset daily statistics (call this at start of each day)"""
        self.daily_losses = 0.0
        self.daily_trades = 0
        logger.info("📊 Daily statistics reset")

    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            'open_positions': len(self.positions),
            'max_positions': self.max_positions,
            'daily_losses': self.daily_losses,
            'max_daily_loss': self.max_daily_loss,
            'daily_trades': self.daily_trades,
            'positions_available': self.max_positions - len(self.positions)
        }
