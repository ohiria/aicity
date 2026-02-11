"""World — Locations & Time System for AICity v2."""

import random
from dataclasses import dataclass, field
from typing import Optional

LOCATIONS = [
    {"id": "parliament", "name": "国会議事堂", "x": 500, "y": 80, "type": "government", "capacity": 20, "icon": "🏛️"},
    {"id": "market", "name": "中央市場", "x": 200, "y": 300, "type": "commerce", "capacity": 30, "icon": "🏪"},
    {"id": "residential_north", "name": "北住宅街", "x": 150, "y": 150, "type": "residential", "capacity": 40, "icon": "🏘️"},
    {"id": "residential_south", "name": "南住宅街", "x": 350, "y": 450, "type": "residential", "capacity": 40, "icon": "🏘️"},
    {"id": "office", "name": "オフィス街", "x": 650, "y": 250, "type": "business", "capacity": 25, "icon": "🏢"},
    {"id": "hospital", "name": "総合病院", "x": 800, "y": 150, "type": "service", "capacity": 20, "icon": "🏥"},
    {"id": "school", "name": "学校", "x": 100, "y": 450, "type": "education", "capacity": 30, "icon": "🏫"},
    {"id": "park", "name": "中央公園", "x": 450, "y": 300, "type": "leisure", "capacity": 50, "icon": "🌳"},
    {"id": "police", "name": "警察署", "x": 700, "y": 400, "type": "government", "capacity": 15, "icon": "🚔"},
    {"id": "court", "name": "裁判所", "x": 600, "y": 400, "type": "government", "capacity": 15, "icon": "⚖️"},
    {"id": "shrine", "name": "神社", "x": 300, "y": 100, "type": "culture", "capacity": 20, "icon": "⛩️"},
    {"id": "restaurant", "name": "レストラン街", "x": 350, "y": 250, "type": "commerce", "capacity": 25, "icon": "🍽️"},
]

LOCATION_MAP = {loc["id"]: loc for loc in LOCATIONS}

SEASONS = ["春", "夏", "秋", "冬"]
WEATHER_BY_SEASON = {
    "春": ["晴れ", "曇り", "小雨", "花曇り", "春風"],
    "夏": ["晴れ", "猛暑", "夕立", "曇り", "蒸し暑い"],
    "秋": ["晴れ", "曇り", "秋雨", "涼風", "紅葉日和"],
    "冬": ["晴れ", "曇り", "雪", "寒波", "霜"],
}


@dataclass
class WorldTime:
    tick: int = 0
    minute: int = 0  # 0-59
    hour: int = 6     # 0-23, start at 6AM
    day: int = 1
    year: int = 2024

    def advance(self, minutes: int = 10):
        self.tick += 1
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1

    @property
    def season(self) -> str:
        day_of_year = self.day % 360
        if day_of_year < 90:
            return "春"
        elif day_of_year < 180:
            return "夏"
        elif day_of_year < 270:
            return "秋"
        else:
            return "冬"

    @property
    def display(self) -> str:
        month = ((self.day - 1) // 30) % 12 + 1
        day_of_month = (self.day - 1) % 30 + 1
        return f"{self.year}年{month}月{day_of_month}日 {self.hour:02d}:{self.minute:02d}"

    def to_dict(self) -> dict:
        return {
            "display": self.display,
            "hour": self.hour,
            "minute": self.minute,
            "day": self.day,
            "season": self.season,
            "weather": self._weather,
        }

    _weather: str = "晴れ"
    _weather_change_tick: int = 0

    def maybe_change_weather(self):
        if self.tick - self._weather_change_tick > random.randint(30, 100):
            self._weather = random.choice(WEATHER_BY_SEASON[self.season])
            self._weather_change_tick = self.tick
