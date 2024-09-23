from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict
import json
from game_runner import run_game
from constants import GAME_RULES
import asyncio

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/start_game")
async def start_game():
    global game_state, game_task
    player1_config = {
        "system_message": "You are an AI player in a farming game. Make decisions to maximize your score.",
    }
    player2_config = {
        "system_message": "You are an AI player in a farming game. Make decisions to maximize your score.",
    }
    
    async def game_stream():
        async for state in run_game(player1_config, player2_config):
            if "game_over" in state:
                game_state["game_over"] = True
                game_state["current_day"] = state.get("day", game_state["current_day"])
                yield json.dumps(state)
            else:
                game_state.update(state)
                if "day" in state:
                    game_state["current_day"] = state["day"]
                yield json.dumps({"day": game_state["current_day"], "message": f"Processed day {game_state['current_day']}"})


    return StreamingResponse(game_stream(), media_type="application/json")

@app.post("/stop_game")
async def stop_game():
    global game_task
    if game_task:
        game_task.cancel()
        await game_task
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