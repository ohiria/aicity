"""Life & Death System — Aging, birth, death, marriage, divorce, sickness."""

import random
import uuid
from typing import List, Dict, Optional
from citizen import Citizen, AVATARS, WORK_LOCATIONS


class LifecycleSystem:
    def __init__(self):
        self.dead_citizens: List[dict] = []  # memorial records
        self.marriages_today: List[dict] = []
        self.births_today: List[dict] = []
        self._last_age_day: int = -1

    def tick(self, world_time, citizen_manager, relationships, news_callback):
        events = []

        # Aging: 1 year per 360 game-days
        current_age_year = world_time.day // 360
        if current_age_year > self._last_age_day:
            self._last_age_day = current_age_year
            for c in list(citizen_manager.citizens.values()):
                c.age += 1

        # Every 10 ticks: check death, sickness, birth, marriage, divorce
        if world_time.tick % 10 != 0:
            return

        self.marriages_today.clear()
        self.births_today.clear()

        for c in list(citizen_manager.citizens.values()):
            # --- Death ---
            died = False
            # Old age (probability ramps after 70)
            if c.age > 70:
                death_chance = (c.age - 70) * 0.003
                if random.random() < death_chance:
                    events.extend(self._kill(c, "老衰", citizen_manager, relationships))
                    died = True
            # Health = 0
            if not died and c.health <= 0:
                events.extend(self._kill(c, "病死", citizen_manager, relationships))
                died = True
            # Random accident
            if not died and random.random() < 0.0003:
                events.extend(self._kill(c, "事故死", citizen_manager, relationships))
                died = True
            if died:
                continue

            # --- Sickness ---
            if random.random() < 0.008:
                c.health = max(0, c.health - random.randint(10, 25))
                c.happiness = max(0, c.happiness - 5)
                if c.health < 40:
                    events.append(f"🏥 {c.name}が体調を崩しています（健康: {c.health}）")
                    news_callback(f"🏥 {c.name}が深刻な体調不良に", "social")

            # Hospital healing boost
            if c.location == "hospital" and c.health < 70:
                c.health = min(100, c.health + 8)

        # --- Marriage ---
        if relationships:
            self._check_marriages(citizen_manager, relationships, events, news_callback)

        # --- Divorce ---
        self._check_divorces(citizen_manager, events, news_callback)

        # --- Birth ---
        self._check_births(citizen_manager, world_time, events, news_callback)

    def _kill(self, c: Citizen, cause: str, citizen_manager, relationships) -> List[str]:
        events = []
        self.dead_citizens.append({
            "name": c.name, "age": c.age, "cause": cause,
            "role": c.role, "id": c.id,
        })

        # Mourn: family happiness drops drastically
        for cid in c.children_ids:
            child = citizen_manager.citizens.get(cid)
            if child:
                child.happiness = max(0, child.happiness - 40)
        for pid in c.parent_ids:
            parent = citizen_manager.citizens.get(pid)
            if parent:
                parent.happiness = max(0, parent.happiness - 50)
        if c.spouse_id:
            spouse = citizen_manager.citizens.get(c.spouse_id)
            if spouse:
                spouse.happiness = max(0, spouse.happiness - 50)
                spouse.spouse_id = None

        cause_emoji = {"老衰": "🕊️", "病死": "💀", "事故死": "⚠️"}
        events.append(f"{cause_emoji.get(cause, '💀')} {c.name}さん（{c.age}歳）が{cause}で亡くなりました")

        # Remove from employer
        from economy import Economy  # avoid circular at module level
        # Just remove from citizens dict
        del citizen_manager.citizens[c.id]
        return events

    def _check_marriages(self, citizen_manager, relationships, events, news_callback):
        singles = [c for c in citizen_manager.citizens.values()
                   if c.spouse_id is None and c.age >= 20]
        random.shuffle(singles)
        paired = set()

        for c in singles:
            if c.id in paired:
                continue
            # Find best relationship partner who is also single
            best_id, best_score = None, 50  # minimum score to marry
            for other in singles:
                if other.id == c.id or other.id in paired or other.gender == c.gender:
                    continue
                score = relationships.get_score(c.id, other.id)
                rel_type = relationships.get_type(c.id, other.id)
                if rel_type == "恋人" and score > best_score:
                    best_score = score
                    best_id = other.id

            if best_id and random.random() < 0.15:
                partner = citizen_manager.citizens.get(best_id)
                if partner:
                    c.spouse_id = partner.id
                    partner.spouse_id = c.id
                    c.happiness = min(100, c.happiness + 20)
                    partner.happiness = min(100, partner.happiness + 20)
                    paired.add(c.id)
                    paired.add(partner.id)
                    self.marriages_today.append({"a": c.name, "b": partner.name})
                    headline = f"💒 {c.name}と{partner.name}が結婚しました！おめでとう！"
                    events.append(headline)
                    news_callback(headline, "social")

    def _check_divorces(self, citizen_manager, events, news_callback):
        checked = set()
        for c in list(citizen_manager.citizens.values()):
            if c.spouse_id and c.spouse_id not in checked and c.id not in checked:
                spouse = citizen_manager.citizens.get(c.spouse_id)
                if spouse and c.happiness < 20 and spouse.happiness < 20 and random.random() < 0.05:
                    c.spouse_id = None
                    spouse.spouse_id = None
                    c.happiness = max(0, c.happiness - 10)
                    spouse.happiness = max(0, spouse.happiness - 10)
                    headline = f"💔 {c.name}と{spouse.name}が離婚しました"
                    events.append(headline)
                    news_callback(headline, "social")
                checked.add(c.id)

    def _check_births(self, citizen_manager, world_time, events, news_callback):
        checked = set()
        for c in list(citizen_manager.citizens.values()):
            if c.spouse_id and c.id not in checked:
                spouse = citizen_manager.citizens.get(c.spouse_id)
                if not spouse:
                    continue
                checked.add(c.id)
                checked.add(spouse.id)

                if c.happiness > 60 and spouse.happiness > 60 and random.random() < 0.01:
                    # Determine parents
                    mother = c if c.gender == "女" else spouse
                    father = c if c.gender == "男" else spouse

                    # Baby!
                    baby_gender = random.choice(["男", "女"])
                    family_name = father.name[0]  # first kanji = family name
                    # try to get family name (first 1-2 chars)
                    for length in [3, 2, 1]:
                        if father.name[:length] in [ci.name[:length] for ci in citizen_manager.citizens.values() if ci.id != father.id]:
                            family_name = father.name[:length]
                            break
                    else:
                        family_name = father.name[:2]

                    baby_names_m = ["太郎", "健", "翔", "蓮", "陽太", "悠人", "颯太"]
                    baby_names_f = ["花", "結衣", "さくら", "凛", "陽菜", "美咲", "愛"]
                    given = random.choice(baby_names_m if baby_gender == "男" else baby_names_f)
                    baby_name = family_name + given

                    # Inherit personality with variation
                    baby_personality = {}
                    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
                        parent_avg = (mother.personality.get(trait, 0.5) + father.personality.get(trait, 0.5)) / 2
                        baby_personality[trait] = max(0.1, min(0.95, parent_avg + random.uniform(-0.15, 0.15)))

                    baby_id = str(uuid.uuid4())
                    baby = Citizen(
                        id=baby_id,
                        name=baby_name,
                        age=0,
                        gender=baby_gender,
                        role="子供",
                        home=mother.home,
                        personality=baby_personality,
                        money=0,
                        health=100,
                        happiness=80,
                        hunger=10,
                        parent_ids=[father.id, mother.id],
                    )
                    baby.set_location(mother.home)
                    citizen_manager.citizens[baby_id] = baby
                    father.children_ids.append(baby_id)
                    mother.children_ids.append(baby_id)

                    self.births_today.append({"name": baby_name, "parents": [father.name, mother.name]})
                    headline = f"👶 {father.name}と{mother.name}に赤ちゃん「{baby_name}」が誕生！"
                    events.append(headline)
                    news_callback(headline, "social")
