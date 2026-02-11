"""Economy — Businesses, market prices, GDP, employment."""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Business:
    name: str
    type: str
    owner_name: str
    owner_id: str = ""
    employee_ids: List[str] = field(default_factory=list)
    revenue: int = 0
    base_salary: int = 500

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "owner": self.owner_name,
            "employees": len(self.employee_ids),
            "revenue": self.revenue,
        }


BUSINESS_DEFS = [
    {"name": "田中農場", "type": "農業", "owner": "田中健一"},
    {"name": "鈴木商店", "type": "小売", "owner": "加藤武"},
    {"name": "中村工房", "type": "製造", "owner": "森田健太"},
    {"name": "佐藤食堂", "type": "飲食", "owner": "佐藤大輔"},
    {"name": "木村雑貨店", "type": "小売", "owner": "木村春香"},
    {"name": "山田テック", "type": "IT", "owner": "井上拓也"},
    {"name": "吉田キッチン", "type": "飲食", "owner": "吉田恵"},
    {"name": "松本アトリエ", "type": "芸術", "owner": "松本麻衣"},
]

BASE_PRICES = {
    "food": 120,
    "housing": 500,
    "clothing": 200,
    "tools": 150,
    "services": 300,
    "entertainment": 250,
}


class Economy:
    def __init__(self):
        self.businesses: List[Business] = []
        self.prices: Dict[str, int] = dict(BASE_PRICES)
        self.gdp: int = 100000
        self.unemployment: float = 5.0
        self.inflation: float = 2.0
        self.tax_rate: int = 8
        self._prev_prices: Dict[str, int] = dict(BASE_PRICES)
        self._daily_revenue: int = 0

    def init_businesses(self, citizen_manager):
        for bdef in BUSINESS_DEFS:
            owner = citizen_manager.get_by_name(bdef["owner"])
            b = Business(
                name=bdef["name"],
                type=bdef["type"],
                owner_name=bdef["owner"],
                owner_id=owner.id if owner else "",
                base_salary=random.randint(400, 700),
            )
            self.businesses.append(b)

        # Assign employees
        unassigned = [c for c in citizen_manager.citizens.values()
                      if c.role not in ("国会議員", "裁判官") and not c.employer]
        random.shuffle(unassigned)
        for c in unassigned:
            # Try to find a matching business
            for b in self.businesses:
                if len(b.employee_ids) < 5 and b.owner_id != c.id:
                    b.employee_ids.append(c.id)
                    c.employer = b.name
                    c.salary = b.base_salary
                    break

    def tick(self, world_time, citizen_manager) -> List[str]:
        events = []

        # Fluctuate prices slightly each tick
        if random.random() < 0.15:
            key = random.choice(list(self.prices.keys()))
            change = random.randint(-10, 10)
            self.prices[key] = max(50, self.prices[key] + change)

        # Pay salaries every game-day at hour 18
        if world_time.hour == 18 and world_time.minute < 10:
            self._pay_salaries(citizen_manager)

        # Generate revenue for businesses
        for b in self.businesses:
            if random.random() < 0.3:
                rev = random.randint(100, 500)
                b.revenue += rev
                self._daily_revenue += rev

        # Update macro stats periodically
        if world_time.tick % 50 == 0:
            self._update_macro(citizen_manager)

        # Price spike event
        if random.random() < 0.002:
            key = random.choice(list(self.prices.keys()))
            self.prices[key] = int(self.prices[key] * 1.3)
            name_map = {"food": "食料品", "housing": "住宅", "clothing": "衣料品",
                        "tools": "工具", "services": "サービス", "entertainment": "娯楽"}
            events.append(f"📈 {name_map[key]}の価格が急騰！")

        return events

    def _pay_salaries(self, citizen_manager):
        for b in self.businesses:
            for eid in b.employee_ids:
                c = citizen_manager.citizens.get(eid)
                if c:
                    c.money += b.base_salary
                    b.revenue -= b.base_salary

    def _update_macro(self, citizen_manager):
        total_money = sum(c.money for c in citizen_manager.citizens.values())
        self.gdp = total_money + sum(b.revenue for b in self.businesses)
        employed = sum(1 for c in citizen_manager.citizens.values() if c.employer)
        total = len(citizen_manager.citizens)
        self.unemployment = round((1 - employed / max(total, 1)) * 100, 1)
        # Inflation from price changes
        total_change = sum(self.prices[k] - BASE_PRICES[k] for k in self.prices)
        self.inflation = round(total_change / len(self.prices) / 10, 1)

    def to_dict(self) -> dict:
        return {
            "gdp": self.gdp,
            "unemployment": self.unemployment,
            "inflation": self.inflation,
            "taxRate": self.tax_rate,
            "prices": dict(self.prices),
            "businesses": [b.to_dict() for b in self.businesses],
        }
