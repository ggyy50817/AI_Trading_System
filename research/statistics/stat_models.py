from dataclasses import dataclass


@dataclass
class TradeStatistics:
    symbol: str = ""
    side: str = ""
    signals: int = 0
    trades: int = 0
    tp3: int = 0
    sl: int = 0
    wins: int = 0
    losses: int = 0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
