"""Citizens — 30 AI citizens with personalities, families, movement, and conversations."""

import random
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from world import LOCATION_MAP

# Avatar mapping by (role, gender)
AVATARS = {
    ("農民", "男"): "👨‍🌾", ("農民", "女"): "👩‍🌾",
    ("商人", "男"): "👨‍💼", ("商人", "女"): "👩‍💼",
    ("職人", "男"): "👷‍♂️", ("職人", "女"): "👷‍♀️",
    ("教師", "男"): "👨‍🏫", ("教師", "女"): "👩‍🏫",
    ("警察官", "男"): "👮‍♂️", ("警察官", "女"): "👮‍♀️",
    ("公務員", "男"): "👨‍💼", ("公務員", "女"): "👩‍💼",
    ("医者", "男"): "👨‍⚕️", ("医者", "女"): "👩‍⚕️",
    ("国会議員", "男"): "🧑‍⚖️", ("国会議員", "女"): "👩‍⚖️",
    ("裁判官", "男"): "👨‍⚖️", ("裁判官", "女"): "👩‍⚖️",
    ("シェフ", "男"): "👨‍🍳", ("シェフ", "女"): "👩‍🍳",
    ("芸術家", "男"): "👨‍🎨", ("芸術家", "女"): "👩‍🎨",
    ("エンジニア", "男"): "👷‍♂️", ("エンジニア", "女"): "👷‍♀️",
}

# Work locations by role
WORK_LOCATIONS = {
    "農民": "market",
    "商人": "market",
    "職人": "office",
    "教師": "school",
    "警察官": "police",
    "公務員": "parliament",
    "医者": "hospital",
    "国会議員": "parliament",
    "裁判官": "court",
    "シェフ": "restaurant",
    "芸術家": "park",
    "エンジニア": "office",
}

# Conversation templates organized by topic
CONV_TEMPLATES = {
    "politics": [
        "最近の政治はどう思いますか？",
        "新しい法案について聞きましたか？",
        "税金が高すぎると思いませんか？",
        "総理大臣の政策、賛成ですか？",
        "次の選挙、誰に投票しますか？",
        "国会の議論、見ましたか？",
        "もっと環境政策が必要だと思います",
        "教育への投資を増やすべきです",
        "治安が良くなったと思いませんか？",
        "福祉制度を見直すべきだと思います",
    ],
    "economy": [
        "最近、物価が上がりましたね",
        "今日は野菜が高いですね",
        "景気が良くなってきた気がします",
        "給料が上がらないのに物価ばかり…",
        "新しいお店ができたみたいですよ",
        "商売の調子はどうですか？",
        "この辺りの家賃、知ってます？",
        "節約しないといけませんね",
        "投資とか考えていますか？",
        "消費税がまた上がるかもしれませんね",
    ],
    "daily": [
        "いい天気ですね！",
        "今日は忙しかったですか？",
        "最近、体調はいかがですか？",
        "お昼、何食べましたか？",
        "週末の予定はありますか？",
        "最近よく眠れますか？",
        "散歩にはいい季節ですね",
        "今日の夕飯、何にしようかな",
        "最近、運動してますか？",
        "疲れが溜まってきました…",
    ],
    "gossip": [
        "聞きましたか？{name}さんが…",
        "{name}さん、最近元気ないみたいですよ",
        "{name}さんと{name2}さん、仲良さそうですね",
        "あの人、転職するらしいですよ",
        "隣の{name}さん、引っ越すって本当？",
        "あの夫婦、喧嘩してたらしいですよ",
        "{name}さんの子供、優秀だって評判です",
        "病院で{name}さんを見かけましたよ",
        "{name}さん、昇進したらしいです",
        "あの店、そろそろ閉まるって噂ですよ",
    ],
    "family": [
        "子供の成長は早いですね",
        "うちの子、最近反抗期で…",
        "家族でどこか行きたいですね",
        "親の介護、大変じゃないですか？",
        "奥さん（旦那さん）元気ですか？",
        "家族の健康が一番大事ですね",
        "子供の教育費、高いですよね",
        "家族サービスしてますか？",
        "実家に帰りたいなあ",
        "家族で食事するのが幸せです",
    ],
    "response_agree": [
        "そうですよね！",
        "本当にそう思います",
        "私もそう感じていました",
        "おっしゃる通りです",
        "まさにその通りですね",
        "同感です！",
    ],
    "response_disagree": [
        "うーん、どうでしょうか…",
        "私はちょっと違う考えです",
        "そうかなあ？",
        "それはどうかと思いますが…",
        "別の見方もあると思います",
    ],
    "response_neutral": [
        "なるほどですね",
        "そういう考え方もありますね",
        "面白い話ですね",
        "初めて聞きました",
        "ふーん、そうなんですか",
        "考えたことなかったです",
    ],
}

MOOD_MAP = {
    (80, 101): "ecstatic",
    (60, 80): "happy",
    (40, 60): "neutral",
    (20, 40): "sad",
    (0, 20): "miserable",
}


def get_mood(happiness: int) -> str:
    for (lo, hi), mood in MOOD_MAP.items():
        if lo <= happiness < hi:
            return mood
    return "neutral"


# Define the 30 citizens
CITIZEN_DEFS = [
    # Family 1: Tanaka family
    {"name": "田中健一", "age": 45, "gender": "男", "role": "農民", "home": "residential_north"},
    {"name": "田中美咲", "age": 42, "gender": "女", "role": "商人", "home": "residential_north"},
    {"name": "田中翔太", "age": 20, "gender": "男", "role": "エンジニア", "home": "residential_north"},
    # Family 2: Suzuki family
    {"name": "鈴木一郎", "age": 50, "gender": "男", "role": "国会議員", "home": "residential_south"},
    {"name": "鈴木花子", "age": 48, "gender": "女", "role": "教師", "home": "residential_south"},
    {"name": "鈴木愛", "age": 22, "gender": "女", "role": "芸術家", "home": "residential_south"},
    # Family 3: Sato family
    {"name": "佐藤大輔", "age": 40, "gender": "男", "role": "シェフ", "home": "residential_south"},
    {"name": "佐藤由美", "age": 38, "gender": "女", "role": "医者", "home": "residential_south"},
    {"name": "佐藤蓮", "age": 18, "gender": "男", "role": "職人", "home": "residential_south"},
    # Family 4: Nakamura family
    {"name": "中村正義", "age": 55, "gender": "男", "role": "国会議員", "home": "residential_north"},
    {"name": "中村幸子", "age": 52, "gender": "女", "role": "公務員", "home": "residential_north"},
    {"name": "中村美月", "age": 25, "gender": "女", "role": "エンジニア", "home": "residential_north"},
    # Other citizens
    {"name": "山田太郎", "age": 60, "gender": "男", "role": "国会議員", "home": "residential_north"},
    {"name": "高橋誠", "age": 35, "gender": "男", "role": "警察官", "home": "residential_south"},
    {"name": "伊藤さくら", "age": 28, "gender": "女", "role": "教師", "home": "residential_north"},
    {"name": "渡辺隆", "age": 65, "gender": "男", "role": "裁判官", "home": "residential_south"},
    {"name": "小林真理", "age": 33, "gender": "女", "role": "医者", "home": "residential_north"},
    {"name": "加藤武", "age": 44, "gender": "男", "role": "商人", "home": "residential_south"},
    {"name": "吉田恵", "age": 29, "gender": "女", "role": "シェフ", "home": "residential_north"},
    {"name": "山本浩二", "age": 52, "gender": "男", "role": "公務員", "home": "residential_south"},
    {"name": "松本麻衣", "age": 26, "gender": "女", "role": "芸術家", "home": "residential_north"},
    {"name": "井上拓也", "age": 38, "gender": "男", "role": "エンジニア", "home": "residential_south"},
    {"name": "木村春香", "age": 31, "gender": "女", "role": "商人", "home": "residential_north"},
    {"name": "斎藤剛", "age": 47, "gender": "男", "role": "国会議員", "home": "residential_south"},
    {"name": "山口美穂", "age": 36, "gender": "女", "role": "警察官", "home": "residential_north"},
    {"name": "森田健太", "age": 41, "gender": "男", "role": "職人", "home": "residential_south"},
    {"name": "藤田あかり", "age": 24, "gender": "女", "role": "公務員", "home": "residential_north"},
    {"name": "岡田勇", "age": 58, "gender": "男", "role": "国会議員", "home": "residential_south"},
    {"name": "長谷川涼子", "age": 34, "gender": "女", "role": "エンジニア", "home": "residential_north"},
    {"name": "石井太一", "age": 27, "gender": "男", "role": "農民", "home": "residential_south"},
]


@dataclass
class Citizen:
    id: str
    name: str
    age: int
    gender: str
    role: str
    home: str  # location id
    personality: Dict[str, float] = field(default_factory=dict)  # Big Five
    location: str = ""
    target_location: str = ""
    x: float = 0
    y: float = 0
    target_x: float = 0
    target_y: float = 0
    money: int = 3000
    health: int = 85
    happiness: int = 65
    hunger: int = 20
    employer: str = ""
    salary: int = 0
    spouse_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    parent_ids: List[str] = field(default_factory=list)
    speaking: Optional[str] = None
    speaking_to: Optional[str] = None
    action: str = "待機中"
    is_external: bool = False
    api_key: Optional[str] = None
    _speak_timer: int = 0

    @property
    def avatar(self) -> str:
        return AVATARS.get((self.role, self.gender), "🧑")

    @property
    def mood(self) -> str:
        return get_mood(self.happiness)

    def get_offset_position(self, loc_id: str) -> tuple:
        loc = LOCATION_MAP[loc_id]
        ox = random.uniform(-25, 25)
        oy = random.uniform(-20, 20)
        return loc["x"] + ox, loc["y"] + oy

    def set_location(self, loc_id: str):
        self.location = loc_id
        self.x, self.y = self.get_offset_position(loc_id)
        self.target_x, self.target_y = self.x, self.y
        self.target_location = loc_id

    def set_target(self, loc_id: str):
        self.target_location = loc_id
        self.target_x, self.target_y = self.get_offset_position(loc_id)

    def move_toward_target(self, speed: float = 15.0):
        if self.location == self.target_location:
            return
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < speed:
            self.x = self.target_x
            self.y = self.target_y
            self.location = self.target_location
        else:
            self.x += dx / dist * speed
            self.y += dy / dist * speed

    def to_dict(self, all_citizens: dict) -> dict:
        spouse_name = None
        children_names = []
        if self.spouse_id and self.spouse_id in all_citizens:
            spouse_name = all_citizens[self.spouse_id].name
        for cid in self.children_ids:
            if cid in all_citizens:
                children_names.append(all_citizens[cid].name)
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "role": self.role,
            "gender": self.gender,
            "location": self.location,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "targetX": round(self.target_x, 1),
            "targetY": round(self.target_y, 1),
            "mood": self.mood,
            "health": self.health,
            "money": self.money,
            "happiness": self.happiness,
            "hunger": self.hunger,
            "action": self.action,
            "speaking": self.speaking,
            "speakingTo": self.speaking_to,
            "family": {
                "spouse": spouse_name,
                "children": children_names,
            },
            "isExternal": self.is_external,
            "avatar": self.avatar,
        }


class CitizenManager:
    def __init__(self):
        self.citizens: Dict[str, Citizen] = {}
        self.conversations: List[dict] = []  # active conversations
        self._init_citizens()
        self._init_families()

    def _init_citizens(self):
        for defn in CITIZEN_DEFS:
            cid = str(uuid.uuid4())
            personality = {
                "openness": random.uniform(0.2, 0.9),
                "conscientiousness": random.uniform(0.2, 0.9),
                "extraversion": random.uniform(0.2, 0.9),
                "agreeableness": random.uniform(0.2, 0.9),
                "neuroticism": random.uniform(0.2, 0.9),
            }
            c = Citizen(
                id=cid,
                name=defn["name"],
                age=defn["age"],
                gender=defn["gender"],
                role=defn["role"],
                home=defn["home"],
                personality=personality,
                money=random.randint(2000, 8000),
                health=random.randint(70, 100),
                happiness=random.randint(50, 85),
                hunger=random.randint(10, 40),
            )
            c.set_location(defn["home"])
            self.citizens[cid] = c

    def _init_families(self):
        by_name = {c.name: c for c in self.citizens.values()}
        families = [
            ("田中健一", "田中美咲", ["田中翔太"]),
            ("鈴木一郎", "鈴木花子", ["鈴木愛"]),
            ("佐藤大輔", "佐藤由美", ["佐藤蓮"]),
            ("中村正義", "中村幸子", ["中村美月"]),
        ]
        for husband_name, wife_name, child_names in families:
            h = by_name[husband_name]
            w = by_name[wife_name]
            h.spouse_id = w.id
            w.spouse_id = h.id
            for cn in child_names:
                child = by_name[cn]
                h.children_ids.append(child.id)
                w.children_ids.append(child.id)
                child.parent_ids = [h.id, w.id]

    def get_by_name(self, name: str) -> Optional[Citizen]:
        for c in self.citizens.values():
            if c.name == name:
                return c
        return None

    def get_by_role(self, role: str) -> List[Citizen]:
        return [c for c in self.citizens.values() if c.role == role]

    def update_movement(self, hour: int):
        """Decide where citizens should go based on time of day."""
        for c in self.citizens.values():
            if c.is_external:
                continue
            if c.location == c.target_location:
                target = self._decide_target(c, hour)
                if target and target != c.location:
                    c.set_target(target)
                    c.action = f"{LOCATION_MAP[target]['name']}へ移動中"
            c.move_toward_target()
            if c.location == c.target_location:
                c.action = self._location_action(c)

    def _decide_target(self, c: Citizen, hour: int) -> Optional[str]:
        # Night (23-6): home
        if hour >= 23 or hour < 6:
            return c.home
        # Morning work (7-11)
        if 7 <= hour < 11:
            if random.random() < 0.05:  # small chance to stay/go elsewhere
                return random.choice(["park", "shrine", "market"])
            return WORK_LOCATIONS.get(c.role, "office")
        # Lunch (11-13)
        if 11 <= hour < 13:
            if random.random() < 0.6:
                return random.choice(["restaurant", "market", "park"])
            return WORK_LOCATIONS.get(c.role, "office")
        # Afternoon work (13-17)
        if 13 <= hour < 17:
            if random.random() < 0.08:
                return random.choice(["park", "market"])
            return WORK_LOCATIONS.get(c.role, "office")
        # Evening (17-22)
        if 17 <= hour < 20:
            choices = [c.home, "park", "restaurant", "shrine", "market"]
            return random.choice(choices)
        # Late evening
        if 20 <= hour < 23:
            if random.random() < 0.7:
                return c.home
            return random.choice(["restaurant", "park"])
        return None

    def _location_action(self, c: Citizen) -> str:
        loc_type = LOCATION_MAP[c.location]["type"]
        actions = {
            "government": ["業務中", "会議に参加中", "書類を確認中"],
            "commerce": ["買い物中", "商談中", "品定め中"],
            "residential": ["自宅で休憩中", "家事中", "くつろぎ中"],
            "business": ["仕事中", "会議中", "資料作成中"],
            "service": ["診察中", "待合室で待機中", "治療中"],
            "education": ["授業中", "勉強中", "準備中"],
            "leisure": ["散歩中", "ベンチで休憩中", "運動中"],
            "culture": ["参拝中", "散策中", "瞑想中"],
        }
        role_actions = {
            "国会議員": ["法案を審議中", "演説中", "政策を検討中"],
            "警察官": ["巡回中", "パトロール中", "報告書を作成中"],
            "医者": ["患者を診察中", "カルテを書いている", "手術準備中"],
            "教師": ["授業中", "テストを採点中", "生徒と面談中"],
            "シェフ": ["料理中", "仕込み中", "メニュー考案中"],
            "裁判官": ["審理中", "判決文を書いている", "法律を調べている"],
        }
        if c.role in role_actions and c.location == WORK_LOCATIONS.get(c.role):
            return random.choice(role_actions[c.role])
        return random.choice(actions.get(loc_type, ["待機中"]))

    def update_needs(self):
        """Update hunger, health, happiness each tick."""
        for c in self.citizens.values():
            c.hunger = min(100, c.hunger + random.randint(0, 2))
            if c.hunger > 70:
                c.health = max(0, c.health - 1)
                c.happiness = max(0, c.happiness - 1)
            if c.location in ("restaurant", "market") and c.hunger > 40 and c.money > 100:
                c.hunger = max(0, c.hunger - 30)
                c.money -= 100
                c.happiness = min(100, c.happiness + 3)
            if c.location == "hospital" and c.health < 60:
                c.health = min(100, c.health + 5)
                c.money -= 200
            if c.location == "park":
                c.happiness = min(100, c.happiness + 1)
            # Clear speaking after timer
            if c.speaking and c._speak_timer > 0:
                c._speak_timer -= 1
                if c._speak_timer <= 0:
                    c.speaking = None
                    c.speaking_to = None

    def generate_conversations(self):
        """Generate conversations between citizens at the same location."""
        self.conversations = []
        # Group citizens by location
        by_loc: Dict[str, List[Citizen]] = {}
        for c in self.citizens.values():
            if c.location == c.target_location:  # only if arrived
                by_loc.setdefault(c.location, []).append(c)

        for loc_id, citizens_at in by_loc.items():
            if len(citizens_at) < 2:
                continue
            # 20% chance per tick that a conversation happens at a location
            if random.random() > 0.20:
                continue
            # Pick 2 citizens
            pair = random.sample(citizens_at, 2)
            c1, c2 = pair
            if c1.speaking or c2.speaking:
                continue

            topic = random.choice(["politics", "economy", "daily", "gossip", "family"])
            msg1 = random.choice(CONV_TEMPLATES[topic])

            # Fill in gossip names
            other_names = [c.name for c in self.citizens.values() if c.name not in (c1.name, c2.name)]
            if "{name}" in msg1:
                msg1 = msg1.replace("{name}", random.choice(other_names))
            if "{name2}" in msg1:
                msg1 = msg1.replace("{name2}", random.choice(other_names))

            # Response
            resp_type = random.choice(["response_agree", "response_disagree", "response_neutral"])
            msg2 = random.choice(CONV_TEMPLATES[resp_type])

            # Maybe a third message
            messages = [
                {"speaker": c1.name, "text": msg1},
                {"speaker": c2.name, "text": msg2},
            ]
            if random.random() < 0.5:
                followup_topic = random.choice(["daily", "economy", "politics"])
                msg3 = random.choice(CONV_TEMPLATES[followup_topic])
                if "{name}" in msg3:
                    msg3 = msg3.replace("{name}", random.choice(other_names))
                if "{name2}" in msg3:
                    msg3 = msg3.replace("{name2}", random.choice(other_names))
                messages.append({"speaker": c1.name, "text": msg3})

            c1.speaking = msg1
            c1.speaking_to = c2.id
            c1._speak_timer = 8
            c2.speaking = msg2
            c2.speaking_to = c1.id
            c2._speak_timer = 8

            self.conversations.append({
                "location": loc_id,
                "participants": [c1.name, c2.name],
                "messages": messages,
            })

    def register_external(self, name: str, role: str, personality: dict) -> Citizen:
        cid = str(uuid.uuid4())
        api_key = str(uuid.uuid4())
        c = Citizen(
            id=cid,
            name=name,
            age=random.randint(20, 50),
            gender="男",
            role=role,
            home="residential_south",
            personality=personality or {},
            is_external=True,
            api_key=api_key,
        )
        c.set_location("residential_south")
        self.citizens[cid] = c
        return c
