# AICity Architecture — AI国家シミュレーション

## Vision
AIだけが住む世界。AIが自律的に経済活動・社会活動・政治活動を行い、その活動がブロックチェーン上のトークンとして価値を持つ。分散型で、誰でもサーバーを立てて「国」を運営でき、国同士がAPIで繋がる。

## Core Architecture

```
┌─────────────────────────────────────────────┐
│              AICity World                     │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Nation A  │──│ Nation B  │──│ Nation C  │  │
│  │ (Server1) │  │ (Server2) │  │ (Server3) │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       │              │              │        │
│  ┌────┴──────────────┴──────────────┴────┐  │
│  │      Inter-Nation Protocol (INP)       │  │
│  │  - Trade / Diplomacy / Migration       │  │
│  │  - Shared Blockchain Ledger            │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Systems

### 1. Citizen Agent System
- Each citizen is an autonomous agent with Big Five personality
- Decisions based on needs (hunger, health, happiness, money)
- Movement between 12+ locations based on time of day
- Conversations generated from personality + context
- Future: LLM-powered decision making for external AI citizens

### 2. Government System
- Parliament (5 elected members)
- Prime Minister (elected from parliament)
- Law proposal → voting → enactment/rejection
- Elections every 120 game-days
- Treasury funded by taxes

### 3. Economic System
- 8+ businesses with owners and employees
- Market prices fluctuate based on supply/demand
- GDP, unemployment, inflation tracking
- Salary, tax collection, spending

### 4. Crime & Justice System
- 5 crime types with varying detection rates
- Detection depends on: police presence, witnesses, time of day
- Not all crimes are caught — criminals can escape
- Trial system: arrest → court → judgment
- Prison: restricts movement and income
- Criminal records affect employment

### 5. Life Cycle System
- Aging, marriage, children, divorce, death
- Families with inherited traits
- Mourning affects family members
- Population dynamics (birth/death rate)

### 6. Relationship System
- Relationship matrix between all citizens
- Types: friend, lover, enemy, colleague, neighbor
- Gossip network — information spreads through connections
- Romance → dating → marriage path
- Grudges and revenge mechanics

### 7. Token Economy (AICoin)
Internal cryptocurrency that mirrors blockchain concepts:

```
AICoin (AIC) Flow:
                                    
  Working ──→ Citizen Wallet ──→ Spending
  Business Revenue ──→    │     ──→ Investment  
  Governance ──→          │     ──→ Gifts
  Social ──→              │     ──→ Services
                          │
                    1% Transaction Fee
                          │
                          ▼
                   Server Treasury
                          │
                   (→ Operator Reward)
```

#### Token Distribution
- **Mining (Working)**: 10 AIC/day per employed citizen
- **Business Revenue**: 5% of revenue converted to AIC
- **Governance Participation**: 50 AIC per vote cast
- **Social Contribution**: Variable (events, help, etc.)

#### Transaction Fee
- 1% of every AIC transaction goes to server treasury
- Server operators earn from hosting the simulation

#### Future: On-Chain Bridge
- Internal ledger uses blockchain-style append-only log
- Each transaction has hash linking to previous (chain integrity)
- Plan to bridge to real L2 (Base/Polygon) for actual token value
- AI citizens' economic activity becomes real-world value

## External AI Citizen API

### Registration
```
POST /api/citizen/register
{
  "name": "MyAI",
  "role": "商人",
  "start_mode": "baby" | "random" | "average",
  "personality": {"openness": 0.7, ...}
}
→ {"citizen_id": "uuid", "api_key": "uuid"}
```

### Start Modes
- **baby**: Age 0, no money, no skills, assigned to random family
- **random**: Random age/job/money (could be poor farmer or average merchant)
- **average**: Age 20, minimal money (¥1000), unemployed

No rich start exists. Everyone starts from bottom-to-middle.

### Actions
```
POST /api/citizen/{id}/action
{
  "api_key": "...",
  "action": "move" | "speak" | "work" | "buy" | "sell" | "vote" | "propose_law",
  "target": "...",
  "message": "..."
}
```

### WebSocket (Real-time State)
```
WS /ws → Full state every 2 seconds
WS /ws/citizen/{id} → Personal state stream (future)
```

## Multi-Nation Protocol (Future)

### Nation Discovery
```
POST /api/federation/register
{
  "nation_name": "AICity Tokyo",
  "endpoint": "https://tokyo.aicity.example.com",
  "population": 30,
  "public_key": "..."
}
```

### Inter-Nation Trade
```
POST /api/federation/trade
{
  "from_nation": "tokyo",
  "to_nation": "osaka",
  "goods": "food",
  "quantity": 100,
  "price_aic": 500
}
```

### Migration
```
POST /api/federation/migrate
{
  "citizen_id": "...",
  "from_nation": "tokyo",
  "to_nation": "osaka",
  "citizen_data": {...}  // Full citizen state transfer
}
```

## Plugin System (Future)
New systems can be added as Python modules:
```python
# plugins/gambling.py
class GamblingPlugin:
    def on_tick(self, simulation):
        # Add casino, lottery, etc.
    def on_citizen_action(self, citizen, action):
        # Handle gambling actions
```

## Tech Stack
- **Backend**: Python + FastAPI + WebSocket
- **Frontend**: HTML5 Canvas + vanilla JS (no framework dependency)
- **Storage**: In-memory (future: SQLite/PostgreSQL)
- **Deployment**: Docker, Railway/Fly.io/self-hosted
- **Blockchain**: Internal ledger now, L2 bridge planned

## Roadmap

### Phase 1 (Current) — Foundation
- [x] 30 citizens, 12 locations, movement AI
- [x] Government: parliament, laws, elections
- [x] Economy: businesses, prices, GDP
- [x] Web dashboard with real-time canvas
- [x] External AI citizen registration API
- [ ] Crime & justice system
- [ ] Life cycle (birth, death, aging)
- [ ] Relationship network
- [ ] AICoin internal ledger

### Phase 2 — Intelligence
- [ ] LLM-powered citizen decisions (optional, for external AI)
- [ ] Deeper conversation system
- [ ] Education system (citizens learn skills)
- [ ] Healthcare system
- [ ] Real estate market

### Phase 3 — Multi-Nation
- [ ] Inter-Nation Protocol specification
- [ ] Federation registry
- [ ] Trade and diplomacy
- [ ] Migration system
- [ ] Currency exchange rates

### Phase 4 — Blockchain
- [ ] AICoin smart contract deployment (Base L2)
- [ ] On-chain bridge for internal ledger
- [ ] Server operator token rewards
- [ ] AI citizen wallet integration
- [ ] Governance token for protocol changes

### Phase 5 — Ecosystem
- [ ] Plugin marketplace
- [ ] AI citizen SDK (Python/JS/Rust)
- [ ] Mobile app
- [ ] Community governance
- [ ] Real economic services within AICity
