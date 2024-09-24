from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from game_runner import run_game
from constants import GAME_RULES
import asyncio

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ActionData(BaseModel):
    name: str
    parameters: Optional[List[str]] = None

class GameStateUpdate(BaseModel):
    day: int
    message: str
    player1_action: Optional[ActionData] = None
    player2_action: Optional[ActionData] = None

# Game state
game_state = {
    "player1": None,
    "player2": None,
    "shared_market": None,
    "game_log": [],
    "current_day": 1,
    "game_over": False
}

# Game control
game_task = None
stop_event = asyncio.Event()  # Initialize stop_event here


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/start_game")
async def start_game():
    global game_state, game_task, stop_event
    if game_task:
        raise HTTPException(status_code=400, detail="Game already in progress")
    
    stop_event.clear()
    player1_config = {"system_message": "You are an AI player in a farming game. Make decisions to maximize your score."}
    player2_config = {"system_message": "You are an AI player in a farming game. Make decisions to maximize your score."}
    
    async def game_stream():
        try:
            async for state in run_game(player1_config, player2_config, stop_event):
                if stop_event.is_set():
                    print("Game stopped")
                    break
                game_state.update(state)
                yield json.dumps({
                    "day": state.get("day", game_state["current_day"]),
                    "message": f"Processed day {state.get('day', game_state['current_day'])}",
                    "player1_action": state.get("player1_action"),
                    "player2_action": state.get("player2_action"),
                    "game_over": state.get("game_over", False)
                })
                if state.get("game_over", False):
                    break
        finally:
            print("Game stream finished")

    async def run_game_task():
        async for _ in game_stream():
            pass

    game_task = asyncio.create_task(run_game_task())
    return StreamingResponse(game_stream(), media_type="application/json")

@app.post("/stop_game")
async def stop_game():
    global game_task, stop_event
    stop_event.set()
    if game_task:
        try:
            await asyncio.wait_for(game_task, timeout=5.0)
        except asyncio.TimeoutError:
            print("Game task didn't finish in time, forcefully cancelling")
            game_task.cancel()
        game_task = None
    return {"message": "Game stopped"}

@app.get("/game_state")
async def get_game_state():
    if game_state["player1"] is None or game_state["player2"] is None:
        raise HTTPException(status_code=400, detail="Game not started")
    return game_state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)