"""Crime & Justice System for AICity v2."""

import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import deque

CRIME_TYPES = {
    "theft":        {"name": "窃盗", "base_detection": 0.40, "base_fine": 500,  "jail_ticks": 30,  "emoji": "🔓"},
    "fraud":        {"name": "詐欺", "base_detection": 0.20, "base_fine": 1500, "jail_ticks": 50,  "emoji": "📄"},
    "embezzlement": {"name": "横領", "base_detection": 0.15, "base_fine": 3000, "jail_ticks": 80,  "emoji": "💰"},
    "assault":      {"name": "暴行", "base_detection": 0.60, "base_fine": 800,  "jail_ticks": 40,  "emoji": "👊"},
    "smuggling":    {"name": "密売", "base_detection": 0.25, "base_fine": 2000, "jail_ticks": 60,  "emoji": "📦"},
}


@dataclass
class Crime:
    id: str
    crime_type: str
    perpetrator_id: str
    perpetrator_name: str
    victim_id: Optional[str]
    victim_name: Optional[str]
    location: str
    tick: int
    detected: bool = False
    status: str = "committed"  # committed, detected, trial, guilty, acquitted, undetected
    proceeds: int = 0
    fine: int = 0
    jail_until: int = 0
    witnesses: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        info = CRIME_TYPES[self.crime_type]
        return {
            "id": self.id,
            "type": info["name"],
            "typeKey": self.crime_type,
            "perpetrator": self.perpetrator_name,
            "perpetratorId": self.perpetrator_id,
            "victim": self.victim_name,
            "victimId": self.victim_id,
            "location": self.location,
            "detected": self.detected,
            "status": self.status,
            "proceeds": self.proceeds,
            "fine": self.fine,
        }


class CrimeSystem:
    def __init__(self):
        self.crimes: deque = deque(maxlen=200)
        self.criminal_records: Dict[str, List[str]] = {}  # citizen_id -> [crime_ids]
        self.imprisoned: Dict[str, int] = {}  # citizen_id -> release_tick

    def tick(self, world_time, citizen_manager, news_callback) -> List[str]:
        events = []

        # Release prisoners
        released = []
        for cid, release_tick in list(self.imprisoned.items()):
            if world_time.tick >= release_tick:
                released.append(cid)
        for cid in released:
            del self.imprisoned[cid]
            c = citizen_manager.citizens.get(cid)
            if c:
                c.set_location(c.home)
                c.action = "出所"
                events.append(f"🔓 {c.name}が刑期を終えて出所しました")

        # Attempt crimes (every few ticks)
        if world_time.tick % 5 == 0:
            for c in list(citizen_manager.citizens.values()):
                if c.id in self.imprisoned or c.is_external:
                    continue
                crime = self._maybe_commit_crime(c, world_time, citizen_manager)
                if crime:
                    self.crimes.appendleft(crime)
                    # Detection
                    detected = self._check_detection(crime, world_time, citizen_manager)
                    if detected:
                        crime.detected = True
                        crime.status = "detected"
                        events.append(self._arrest_and_trial(crime, world_time, citizen_manager))
                    else:
                        crime.status = "undetected"
                        # Criminal keeps proceeds
                        c.money += crime.proceeds
                        # Rumor spread — witnesses may gossip later
                        if crime.witnesses:
                            events.append(
                                f"👁️ {crime.perpetrator_name}の{CRIME_TYPES[crime.crime_type]['name']}は発覚しなかった…"
                            )

        for e in events:
            news_callback(e, "crime")
        return events

    def _maybe_commit_crime(self, c, world_time, citizen_manager) -> Optional[Crime]:
        p = c.personality
        # Low money + low conscientiousness → theft
        if c.money < 500 and p.get("conscientiousness", 0.5) < 0.35 and random.random() < 0.08:
            victim = self._pick_victim(c, citizen_manager)
            proceeds = random.randint(100, 800)
            if victim:
                victim.money = max(0, victim.money - proceeds)
            return self._make_crime("theft", c, victim, proceeds, world_time)

        # High neuroticism + low happiness → assault
        if p.get("neuroticism", 0.5) > 0.7 and c.happiness < 30 and random.random() < 0.06:
            victim = self._pick_victim(c, citizen_manager)
            if victim:
                victim.health = max(0, victim.health - random.randint(10, 30))
                victim.happiness = max(0, victim.happiness - 15)
            return self._make_crime("assault", c, victim, 0, world_time)

        # Merchant + low agreeableness → fraud
        if c.role == "商人" and p.get("agreeableness", 0.5) < 0.3 and random.random() < 0.04:
            victim = self._pick_victim(c, citizen_manager)
            proceeds = random.randint(500, 2000)
            if victim:
                victim.money = max(0, victim.money - proceeds)
            return self._make_crime("fraud", c, victim, proceeds, world_time)

        # Employer + low conscientiousness → embezzlement
        if c.employer and p.get("conscientiousness", 0.5) < 0.25 and random.random() < 0.02:
            proceeds = random.randint(1000, 5000)
            return self._make_crime("embezzlement", c, None, proceeds, world_time)

        # Low agreeableness + specific locations → smuggling
        if c.location == "market" and p.get("agreeableness", 0.5) < 0.3 and p.get("openness", 0.5) > 0.6 and random.random() < 0.03:
            proceeds = random.randint(800, 3000)
            return self._make_crime("smuggling", c, None, proceeds, world_time)

        return None

    def _pick_victim(self, criminal, citizen_manager):
        at_loc = [c for c in citizen_manager.citizens.values()
                  if c.location == criminal.location and c.id != criminal.id and c.id not in self.imprisoned]
        return random.choice(at_loc) if at_loc else None

    def _make_crime(self, crime_type, perp, victim, proceeds, world_time) -> Crime:
        from world import LOCATION_MAP
        # Gather witnesses
        witnesses = []  # filled during detection
        crime = Crime(
            id=str(uuid.uuid4()),
            crime_type=crime_type,
            perpetrator_id=perp.id,
            perpetrator_name=perp.name,
            victim_id=victim.id if victim else None,
            victim_name=victim.name if victim else None,
            location=perp.location,
            tick=world_time.tick,
            proceeds=proceeds,
        )
        return crime

    def _check_detection(self, crime: Crime, world_time, citizen_manager) -> bool:
        info = CRIME_TYPES[crime.crime_type]
        rate = info["base_detection"]

        # Police at location boost detection
        police_count = sum(1 for c in citizen_manager.citizens.values()
                          if c.role == "警察官" and c.location == crime.location)
        rate += police_count * 0.15

        # Witnesses boost detection
        witnesses = [c for c in citizen_manager.citizens.values()
                     if c.location == crime.location and c.id != crime.perpetrator_id]
        crime.witnesses = [w.id for w in witnesses[:5]]
        rate += len(witnesses) * 0.03

        # Night penalty
        if world_time.hour >= 22 or world_time.hour < 6:
            rate *= 0.5

        return random.random() < min(rate, 0.95)

    def _arrest_and_trial(self, crime: Crime, world_time, citizen_manager) -> str:
        info = CRIME_TYPES[crime.crime_type]
        perp = citizen_manager.citizens.get(crime.perpetrator_id)
        if not perp:
            return ""

        # Move to police station
        perp.set_location("police")
        perp.action = "逮捕された"

        # Find a judge
        judges = citizen_manager.get_by_role("裁判官")
        judge = judges[0] if judges else None

        # Evidence strength
        evidence = 0.5 + len(crime.witnesses) * 0.1
        if judge:
            # Judge personality affects verdict
            evidence += judge.personality.get("conscientiousness", 0.5) * 0.2
            evidence -= judge.personality.get("agreeableness", 0.5) * 0.1

        guilty = random.random() < min(evidence, 0.92)

        if guilty:
            crime.status = "guilty"
            crime.fine = info["base_fine"]
            jail_ticks = info["jail_ticks"]
            crime.jail_until = world_time.tick + jail_ticks

            perp.money = max(0, perp.money - crime.fine)
            self.imprisoned[perp.id] = crime.jail_until
            self.criminal_records.setdefault(perp.id, []).append(crime.id)
            perp.happiness = max(0, perp.happiness - 25)
            perp.action = "服役中"

            victim_part = f"（被害者: {crime.victim_name}）" if crime.victim_name else ""
            return (
                f"⚖️ {perp.name}が{info['name']}で有罪判決！"
                f"罰金{crime.fine}円・禁固{jail_ticks}ティック{victim_part}"
            )
        else:
            crime.status = "acquitted"
            perp.set_location(perp.home)
            return f"⚖️ {perp.name}の{info['name']}裁判 — 無罪判決"

    def is_imprisoned(self, citizen_id: str) -> bool:
        return citizen_id in self.imprisoned

    def has_criminal_record(self, citizen_id: str) -> bool:
        return citizen_id in self.criminal_records

    def get_recent_crimes(self, limit: int = 50) -> List[dict]:
        return [c.to_dict() for c in list(self.crimes)[:limit]]

    def get_gossip_targets(self) -> List[Crime]:
        """Return recent undetected crimes that witnesses know about — for gossip system."""
        return [c for c in self.crimes if c.status == "undetected" and c.witnesses]
