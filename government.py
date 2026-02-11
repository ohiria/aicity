"""Government — Political system, laws, elections, treasury."""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict

LAW_POOL = [
    ("最低賃金引上法", "最低賃金を15%引き上げる"),
    ("デジタル化推進法", "行政手続きの完全デジタル化"),
    ("子育て支援法", "子供一人あたり月額5万円の支給"),
    ("再生エネルギー法", "2030年までに再生エネルギー50%達成"),
    ("観光促進法", "観光産業への補助金拡大"),
    ("医療費削減法", "医療費の自己負担を20%に引き下げ"),
    ("労働時間規制法", "週35時間労働制の導入"),
    ("農業支援法", "農家への直接補助金制度"),
    ("交通インフラ整備法", "新しい鉄道路線の建設"),
    ("文化振興法", "芸術・文化活動への助成金倍増"),
    ("防災対策強化法", "災害対策予算の大幅増額"),
    ("高齢者福祉法", "高齢者介護の無償化"),
    ("IT教育推進法", "全学校でプログラミング教育必修化"),
    ("食品安全基準強化法", "食品安全検査の厳格化"),
    ("住宅支援法", "若者向け住宅ローン金利優遇"),
    ("起業支援法", "新規起業への税制優遇措置"),
]


@dataclass
class Law:
    name: str
    description: str
    status: str = "proposed"  # proposed, voting, enacted, rejected
    votes_for: int = 0
    votes_against: int = 0
    proposed_by: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "votesFor": self.votes_for,
            "votesAgainst": self.votes_against,
        }


class Government:
    def __init__(self):
        self.laws: List[Law] = [
            Law("消費税法", "消費税8%", status="enacted"),
            Law("教育基本法", "義務教育の保障と教育の機会均等", status="enacted"),
            Law("環境保護法", "環境汚染の防止と自然保護", status="enacted"),
        ]
        self.active_bill: Optional[Law] = None
        self.parliament_ids: List[str] = []
        self.prime_minister_id: Optional[str] = None
        self.treasury: int = 50000
        self.election_day: int = 120
        self.next_proposal_tick: int = 0
        self._vote_tick: int = 0
        self._used_laws: set = set()

    def init_parliament(self, citizen_manager):
        """Set up parliament from citizens with role=国会議員."""
        members = citizen_manager.get_by_role("国会議員")
        self.parliament_ids = [m.id for m in members[:5]]
        if self.parliament_ids:
            self.prime_minister_id = self.parliament_ids[0]

    def tick(self, world_time, citizen_manager) -> List[str]:
        """Process government actions. Returns news events."""
        events = []

        # Elections
        if world_time.day >= self.election_day:
            events.extend(self._hold_election(citizen_manager))
            self.election_day = world_time.day + 120

        # Propose new law
        if self.active_bill is None and world_time.tick >= self.next_proposal_tick:
            event = self._propose_law(citizen_manager)
            if event:
                events.append(event)
            self.next_proposal_tick = world_time.tick + random.randint(150, 250)

        # Vote on active bill
        if self.active_bill and self.active_bill.status == "voting":
            if world_time.tick >= self._vote_tick:
                events.extend(self._process_vote(citizen_manager))

        # Tax collection (every game-day)
        if world_time.hour == 0 and world_time.minute < 10:
            self._collect_taxes(citizen_manager)

        return events

    def _propose_law(self, citizen_manager) -> Optional[str]:
        available = [(n, d) for n, d in LAW_POOL if n not in self._used_laws]
        if not available:
            self._used_laws.clear()
            available = LAW_POOL[:]
        if not self.parliament_ids:
            return None
        proposer_id = random.choice(self.parliament_ids)
        proposer = citizen_manager.citizens.get(proposer_id)
        if not proposer:
            return None
        name, desc = random.choice(available)
        self._used_laws.add(name)
        self.active_bill = Law(name=name, description=desc, status="voting", proposed_by=proposer.name)
        self._vote_tick = 0  # vote immediately over next few ticks
        return f"🏛️ {proposer.name}議員が「{name}」を提案"

    def _process_vote(self, citizen_manager) -> List[str]:
        events = []
        bill = self.active_bill
        if not bill:
            return events

        # Each parliament member votes
        for pid in self.parliament_ids:
            c = citizen_manager.citizens.get(pid)
            if not c:
                continue
            # Vote based on personality (agreeableness + some randomness)
            agree_chance = c.personality.get("agreeableness", 0.5) * 0.5 + 0.3
            if random.random() < agree_chance:
                bill.votes_for += 1
            else:
                bill.votes_against += 1

        # Decide
        if bill.votes_for > bill.votes_against:
            bill.status = "enacted"
            self.laws.append(bill)
            events.append(f"🏛️ 「{bill.name}」が可決（賛成{bill.votes_for}、反対{bill.votes_against}）")
        else:
            bill.status = "rejected"
            events.append(f"❌ 「{bill.name}」が否決（賛成{bill.votes_for}、反対{bill.votes_against}）")

        self.active_bill = None
        return events

    def _hold_election(self, citizen_manager) -> List[str]:
        # Simple election: pick new PM from parliament
        if self.parliament_ids:
            self.prime_minister_id = random.choice(self.parliament_ids)
            pm = citizen_manager.citizens.get(self.prime_minister_id)
            if pm:
                return [f"🗳️ 選挙実施！{pm.name}が新しい総理大臣に就任"]
        return ["🗳️ 選挙が実施されました"]

    def _collect_taxes(self, citizen_manager):
        total = 0
        for c in citizen_manager.citizens.values():
            tax = int(c.money * 0.001)  # small daily tax
            c.money -= tax
            total += tax
        self.treasury += total

    def to_dict(self, citizen_manager) -> dict:
        pm = None
        if self.prime_minister_id:
            c = citizen_manager.citizens.get(self.prime_minister_id)
            if c:
                pm = {"name": c.name, "party": "国民党"}

        members = []
        for pid in self.parliament_ids:
            c = citizen_manager.citizens.get(pid)
            if c:
                members.append({"name": c.name, "party": "国民党"})

        return {
            "primeMinister": pm,
            "parliamentMembers": members,
            "laws": [l.to_dict() for l in self.laws],
            "activeBill": self.active_bill.to_dict() if self.active_bill else None,
            "treasury": self.treasury,
            "nextElection": f"Day {self.election_day}",
        }
