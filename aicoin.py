"""AICoin Token & Ledger System."""

import hashlib
import time
from typing import Dict, List
from collections import deque
from dataclasses import dataclass


@dataclass
class Transaction:
    tx_from: str  # citizen_id or "system"
    tx_to: str    # citizen_id or "treasury"
    amount: float
    reason: str
    timestamp: int  # game tick
    prev_hash: str = ""
    tx_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.tx_from}:{self.tx_to}:{self.amount}:{self.reason}:{self.timestamp}:{self.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self, citizen_manager=None) -> dict:
        from_name = self.tx_from
        to_name = self.tx_to
        if citizen_manager:
            fc = citizen_manager.citizens.get(self.tx_from)
            if fc:
                from_name = fc.name
            tc = citizen_manager.citizens.get(self.tx_to)
            if tc:
                to_name = tc.name
        return {
            "from": from_name,
            "to": to_name,
            "amount": self.amount,
            "reason": self.reason,
            "tick": self.timestamp,
            "hash": self.tx_hash,
        }


class TokenSystem:
    def __init__(self):
        self.wallets: Dict[str, float] = {}  # citizen_id → AIC balance
        self.treasury: float = 10000.0  # server treasury
        self.total_supply: float = 10000.0
        self.ledger: deque = deque(maxlen=500)
        self._last_hash: str = "genesis"
        self.fee_rate: float = 0.01  # 1% transaction fee

    def init_wallets(self, citizen_manager):
        for cid in citizen_manager.citizens:
            self.wallets[cid] = 100.0  # starting AIC
            self.total_supply += 100.0

    def _record(self, tx_from: str, tx_to: str, amount: float, reason: str, tick: int):
        tx = Transaction(
            tx_from=tx_from, tx_to=tx_to, amount=round(amount, 2),
            reason=reason, timestamp=tick, prev_hash=self._last_hash,
        )
        tx.tx_hash = tx.compute_hash()
        self._last_hash = tx.tx_hash
        self.ledger.appendleft(tx)

    def transfer(self, from_id: str, to_id: str, amount: float, reason: str, tick: int) -> bool:
        if from_id != "system" and self.wallets.get(from_id, 0) < amount:
            return False
        fee = round(amount * self.fee_rate, 2)
        net = round(amount - fee, 2)

        if from_id != "system":
            self.wallets[from_id] = round(self.wallets.get(from_id, 0) - amount, 2)
        else:
            self.total_supply += amount

        if to_id == "treasury":
            self.treasury += net
        else:
            self.wallets[to_id] = round(self.wallets.get(to_id, 0) + net, 2)

        self.treasury += fee
        self._record(from_id, to_id, amount, reason, tick)
        return True

    def reward(self, citizen_id: str, amount: float, reason: str, tick: int):
        """Mint new AIC as reward."""
        self.transfer("system", citizen_id, amount, reason, tick)

    def tick(self, world_time, citizen_manager, government, news_callback):
        # Daily work rewards (every game-day at hour 17)
        if world_time.hour == 17 and world_time.minute < 10:
            for c in citizen_manager.citizens.values():
                if c.employer:
                    self.reward(c.id, 2.0, "労働報酬", world_time.tick)
                # Ensure wallet exists for new citizens
                if c.id not in self.wallets:
                    self.wallets[c.id] = 0.0

        # Governance participation reward (voting-related, simplified)
        if world_time.tick % 100 == 0:
            for pid in government.parliament_ids:
                if pid in self.wallets:
                    self.reward(pid, 5.0, "議会参加", world_time.tick)

        # Occasional business revenue → AIC
        if world_time.tick % 25 == 0:
            from economy import Economy
            for c in citizen_manager.citizens.values():
                # Business owners get extra AIC
                if c.role in ("商人", "シェフ") and random.random() < 0.3:
                    self.reward(c.id, 3.0, "事業収益", world_time.tick)

    def get_balance(self, citizen_id: str) -> float:
        return round(self.wallets.get(citizen_id, 0.0), 2)

    def get_recent_transactions(self, limit: int = 50, citizen_manager=None) -> List[dict]:
        return [tx.to_dict(citizen_manager) for tx in list(self.ledger)[:limit]]

    def to_dict(self, citizen_manager=None) -> dict:
        return {
            "totalSupply": round(self.total_supply, 2),
            "treasury": round(self.treasury, 2),
            "recentTransactions": self.get_recent_transactions(10, citizen_manager),
        }


import random  # needed for tick
