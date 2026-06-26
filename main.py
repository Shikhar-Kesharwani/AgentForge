from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import json

from agent.loop import run_agent_loop

load_dotenv()

app = FastAPI(title="AgentForge")

# Mount static files for the frontend
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Convert history into a serializable format for the loop if needed,
    # or just pass it straight in.
    history_dict = [{"role": msg.role, "content": msg.content} for msg in req.history]
    
    def event_stream():
        for step in run_agent_loop(req.message, history=history_dict):
            # Send each step as an SSE event
            yield f"data: {json.dumps(step)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
