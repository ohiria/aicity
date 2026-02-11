"""Simulation — Main game loop tying everything together."""

import asyncio
from typing import List, Dict
from collections import deque

from world import WorldTime, LOCATIONS
from citizen import CitizenManager
from government import Government
from economy import Economy


class Simulation:
    def __init__(self):
        self.time = WorldTime()
        self.citizens = CitizenManager()
        self.government = Government()
        self.economy = Economy()
        self.news: deque = deque(maxlen=50)
        self.event_log: deque = deque(maxlen=50)
        self.running = False

        # Initialize systems
        self.government.init_parliament(self.citizens)
        self.economy.init_businesses(self.citizens)

    def tick(self):
        """One simulation tick = 10 game minutes."""
        self.time.advance(10)
        self.time.maybe_change_weather()

        # Move citizens
        self.citizens.update_movement(self.time.hour)
        self.citizens.update_needs()

        # Conversations (every few ticks)
        if self.time.tick % 3 == 0:
            self.citizens.generate_conversations()

        # Government
        gov_events = self.government.tick(self.time, self.citizens)
        for e in gov_events:
            self._add_news(e, "politics")

        # Economy
        econ_events = self.economy.tick(self.time, self.citizens)
        for e in econ_events:
            self._add_news(e, "economy")

        # Random life events
        if self.time.tick % 20 == 0:
            self._random_life_event()

    def _add_news(self, text: str, news_type: str = "general"):
        entry = {
            "time": f"{self.time.hour:02d}:{self.time.minute:02d}",
            "text": text,
            "type": news_type,
        }
        self.news.appendleft(entry)
        self.event_log.appendleft(entry)

    def _random_life_event(self):
        import random
        events = [
            ("🎉 {name}さんが昇進しました！", "social"),
            ("🏥 {name}さんが体調を崩しました", "social"),
            ("🎵 {name}さんが公園で演奏しています", "culture"),
            ("🍜 {name}さんが新メニューを開発", "economy"),
            ("📚 {name}さんが新しい本を出版", "culture"),
            ("🏃 {name}さんがマラソン大会で優勝", "social"),
            ("🌸 神社でお祭りが開催中", "culture"),
            ("🎨 {name}さんの展覧会が好評", "culture"),
        ]
        template, etype = random.choice(events)
        citizens = list(self.citizens.citizens.values())
        c = random.choice(citizens)
        text = template.replace("{name}", c.name)
        self._add_news(text, etype)

    def get_state(self) -> dict:
        """Full state snapshot for WebSocket."""
        citizen_list = [c.to_dict(self.citizens.citizens) for c in self.citizens.citizens.values()]
        locations = [{"id": l["id"], "name": l["name"], "x": l["x"], "y": l["y"],
                      "type": l["type"], "icon": l["icon"]} for l in LOCATIONS]

        ext_count = sum(1 for c in self.citizens.citizens.values() if c.is_external)
        all_citizens = list(self.citizens.citizens.values())
        avg_happy = sum(c.happiness for c in all_citizens) / max(len(all_citizens), 1)
        avg_health = sum(c.health for c in all_citizens) / max(len(all_citizens), 1)
        avg_wealth = sum(c.money for c in all_citizens) / max(len(all_citizens), 1)

        return {
            "tick": self.time.tick,
            "time": self.time.to_dict(),
            "locations": locations,
            "citizens": citizen_list,
            "conversations": self.citizens.conversations,
            "government": self.government.to_dict(self.citizens),
            "economy": self.economy.to_dict(),
            "news": list(self.news)[:20],
            "stats": {
                "population": len(all_citizens),
                "externalCitizens": ext_count,
                "avgHappiness": round(avg_happy, 1),
                "avgHealth": round(avg_health, 1),
                "avgWealth": round(avg_wealth),
                "day": self.time.day,
            },
        }

    async def run(self):
        """Main simulation loop — 1 tick per second."""
        self.running = True
        while self.running:
            self.tick()
            await asyncio.sleep(1)

    def stop(self):
        self.running = False
