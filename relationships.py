"""Relationship System — Social bonds, romance, grudges, gossip."""

import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class RelationshipSystem:
    def __init__(self):
        # (id_a, id_b) → score; always store with min(a,b) first
        self.scores: Dict[Tuple[str, str], int] = {}
        # (id_a, id_b) → type override
        self.types: Dict[Tuple[str, str], str] = {}
        # citizen_id → set of crime_ids they know about (gossip)
        self.known_crimes: Dict[str, set] = defaultdict(set)
        # citizen_id → {target_id: reason} grudges
        self.grudges: Dict[str, Dict[str, str]] = defaultdict(dict)

    def _key(self, a: str, b: str) -> Tuple[str, str]:
        return (min(a, b), max(a, b))

    def get_score(self, a: str, b: str) -> int:
        return self.scores.get(self._key(a, b), 0)

    def set_score(self, a: str, b: str, val: int):
        self.scores[self._key(a, b)] = max(-100, min(100, val))

    def change_score(self, a: str, b: str, delta: int):
        k = self._key(a, b)
        cur = self.scores.get(k, 0)
        self.scores[k] = max(-100, min(100, cur + delta))

    def get_type(self, a: str, b: str) -> str:
        k = self._key(a, b)
        if k in self.types:
            return self.types[k]
        score = self.scores.get(k, 0)
        if score >= 70:
            return "友人"
        elif score >= 40:
            return "同僚"
        elif score <= -50:
            return "敵"
        elif score <= -20:
            return "隣人"
        return "知人"

    def set_type(self, a: str, b: str, rtype: str):
        self.types[self._key(a, b)] = rtype

    def tick(self, world_time, citizen_manager, crime_system, news_callback):
        if world_time.tick % 4 != 0:
            return

        citizens = list(citizen_manager.citizens.values())
        # Group by location
        by_loc: Dict[str, list] = defaultdict(list)
        for c in citizens:
            if c.location == c.target_location:
                by_loc[c.location].append(c)

        # Same-location interaction: small relationship boost
        for loc_id, group in by_loc.items():
            if len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    if random.random() < 0.1:
                        # Coworker bonus
                        bonus = 1
                        if a.employer and a.employer == b.employer:
                            bonus = 2
                        # Personality compatibility
                        compat = 1.0 - abs(a.personality.get("extraversion", 0.5) - b.personality.get("extraversion", 0.5))
                        bonus = int(bonus * compat + 0.5)
                        self.change_score(a.id, b.id, max(1, bonus))

        # Romance: high relationship → lover → potential marriage handled by lifecycle
        for (a_id, b_id), score in list(self.scores.items()):
            if score >= 60 and self._key(a_id, b_id) not in self.types:
                ca = citizen_manager.citizens.get(a_id)
                cb = citizen_manager.citizens.get(b_id)
                if ca and cb and ca.gender != cb.gender and ca.spouse_id is None and cb.spouse_id is None:
                    if ca.age >= 18 and cb.age >= 18 and random.random() < 0.05:
                        self.set_type(a_id, b_id, "恋人")
                        news_callback(f"💕 {ca.name}と{cb.name}が交際を始めました", "social")

        # Crime impact on relationships
        if crime_system:
            for crime in list(crime_system.crimes)[:20]:
                if crime.victim_id and crime.perpetrator_id:
                    self.change_score(crime.perpetrator_id, crime.victim_id, -20)
                    self.grudges[crime.victim_id][crime.perpetrator_id] = crime.crime_type

            # Gossip: witnesses spread crime knowledge to friends
            for crime in crime_system.get_gossip_targets():
                for wid in crime.witnesses:
                    self.known_crimes[wid].add(crime.id)
                    # Spread to friends
                    for (a, b), score in list(self.scores.items()):
                        if score >= 30:
                            friend_id = b if a == wid else (a if b == wid else None)
                            if friend_id and random.random() < 0.15:
                                self.known_crimes[friend_id].add(crime.id)
                                # Hearing about crime lowers opinion of criminal
                                self.change_score(friend_id, crime.perpetrator_id, -5)

    def get_relationships_for(self, citizen_id: str, citizen_manager) -> List[dict]:
        result = []
        for (a, b), score in self.scores.items():
            other_id = None
            if a == citizen_id:
                other_id = b
            elif b == citizen_id:
                other_id = a
            if other_id:
                other = citizen_manager.citizens.get(other_id)
                if other:
                    result.append({
                        "citizenId": other_id,
                        "name": other.name,
                        "score": score,
                        "type": self.get_type(citizen_id, other_id),
                    })
        result.sort(key=lambda x: -x["score"])
        return result[:20]

    def get_summary_for(self, citizen_id: str, citizen_manager) -> dict:
        rels = self.get_relationships_for(citizen_id, citizen_manager)
        friends = [r for r in rels if r["score"] >= 40]
        enemies = [r for r in rels if r["score"] <= -30]
        lover = [r for r in rels if r["type"] == "恋人"]
        return {
            "friends": len(friends),
            "enemies": len(enemies),
            "lover": lover[0]["name"] if lover else None,
            "topFriend": friends[0]["name"] if friends else None,
            "worstEnemy": enemies[0]["name"] if enemies else None,
        }

    def init_family_bonds(self, citizen_manager):
        """Set initial high scores for family members."""
        for c in citizen_manager.citizens.values():
            if c.spouse_id:
                self.set_score(c.id, c.spouse_id, 80)
                self.set_type(c.id, c.spouse_id, "恋人")
            for child_id in c.children_ids:
                self.set_score(c.id, child_id, 75)
            for pid in c.parent_ids:
                self.set_score(c.id, pid, 70)
