"""FastAPI application for AICity v2."""

import os
import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from simulation import Simulation

app = FastAPI(title="AICity v2")
sim = Simulation()

TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"


@app.on_event("startup")
async def startup():
    asyncio.create_task(sim.run())


@app.on_event("shutdown")
async def shutdown():
    sim.stop()


@app.get("/", response_class=HTMLResponse)
async def index():
    if TEMPLATE_PATH.exists():
        return HTMLResponse(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AICity v2 — template not found</h1>")


@app.get("/api/status")
async def api_status():
    return {
        "status": "running",
        "tick": sim.time.tick,
        "population": len(sim.citizens.citizens),
        "day": sim.time.day,
    }


@app.get("/api/citizens")
async def api_citizens():
    return [c.to_dict(sim.citizens.citizens) for c in sim.citizens.citizens.values()]


@app.get("/api/government")
async def api_government():
    return sim.government.to_dict(sim.citizens)


@app.get("/api/economy")
async def api_economy():
    return sim.economy.to_dict()


class RegisterRequest(BaseModel):
    name: str
    role: str = "公務員"
    personality: Optional[dict] = None


@app.post("/api/citizen/register")
async def register_citizen(req: RegisterRequest):
    c = sim.citizens.register_external(req.name, req.role, req.personality or {})
    sim._add_news(f"🆕 新しい市民「{c.name}」が登録されました", "social")
    return {"citizen_id": c.id, "api_key": c.api_key}


class ActionRequest(BaseModel):
    api_key: str
    action: str  # "move", "speak", "work"
    target: Optional[str] = None
    message: Optional[str] = None


@app.post("/api/citizen/{citizen_id}/action")
async def citizen_action(citizen_id: str, req: ActionRequest):
    c = sim.citizens.citizens.get(citizen_id)
    if not c or not c.is_external:
        raise HTTPException(404, "Citizen not found")
    if c.api_key != req.api_key:
        raise HTTPException(403, "Invalid API key")

    if req.action == "move" and req.target:
        from world import LOCATION_MAP
        if req.target in LOCATION_MAP:
            c.set_target(req.target)
            c.action = f"{LOCATION_MAP[req.target]['name']}へ移動中"
            return {"status": "moving", "target": req.target}
        raise HTTPException(400, "Invalid location")
    elif req.action == "speak" and req.message:
        c.speaking = req.message
        c._speak_timer = 10
        c.action = "発言中"
        return {"status": "speaking"}
    elif req.action == "work":
        c.money += 100
        c.hunger += 5
        c.action = "働いている"
        return {"status": "working", "money": c.money}

    raise HTTPException(400, "Invalid action")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            state = sim.get_state()
            await ws.send_text(json.dumps(state, ensure_ascii=False))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
