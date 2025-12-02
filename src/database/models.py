from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os
import threading

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pair = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # buy or sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    profit_loss = Column(Float, default=0.0)
    profit_loss_percent = Column(Float, default=0.0)
    status = Column(String(20), default='open')  # open, closed
    strategy = Column(String(50))
    ai_confidence = Column(Float)
    notes = Column(Text)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pair': self.pair,
            'side': self.side,
            'amount': self.amount,
            'price': self.price,
            'total': self.total,
            'profit_loss': self.profit_loss,
            'profit_loss_percent': self.profit_loss_percent,
            'status': self.status,
            'strategy': self.strategy,
            'ai_confidence': self.ai_confidence,
            'notes': self.notes
        }

class Balance(Base):
    __tablename__ = 'balances'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    in_positions = Column(Float, default=0.0)
    total_profit_loss = Column(Float, default=0.0)
    total_profit_loss_percent = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'total_balance': self.total_balance,
            'available_balance': self.available_balance,
            'in_positions': self.in_positions,
            'total_profit_loss': self.total_profit_loss,
            'total_profit_loss_percent': self.total_profit_loss_percent,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        }

class AIAnalysis(Base):
    __tablename__ = 'ai_analysis'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pair = Column(String(20), nullable=False)
    recommendation = Column(String(10))  # buy, sell, hold
    confidence = Column(Float)
    reasoning = Column(Text)
    market_data = Column(Text)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pair': self.pair,
            'recommendation': self.recommendation,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }

# Database initialization
engine = None
Session = None
_session_factory = None

def init_db(db_path='data/trading_bot.db'):
    global engine, Session, _session_factory

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else 'data', exist_ok=True)

    # Use check_same_thread=False for SQLite to allow multi-threading
    # With proper session management, this is safe
    engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={'check_same_thread': False},
        pool_pre_ping=True  # Verify connections before using them
    )
    Base.metadata.create_all(engine)

    # Create a session factory
    _session_factory = sessionmaker(bind=engine)

    # Use scoped_session for thread-safe sessions
    Session = scoped_session(_session_factory)

    return Session()

def get_db_session():
    """
    Get a new database session.
    This should be used by Flask routes to avoid database locking issues.
    Remember to close the session after use.
    """
    global _session_factory

    if _session_factory is None:
        init_db()

    return _session_factory()
