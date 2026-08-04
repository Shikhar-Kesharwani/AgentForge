from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import json
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from agent.loop import run_agent_loop

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AgentForge")

# Setup CORS for decoupled frontend deployment (Vercel etc)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup API Key Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Depends(api_key_header)):
    # Fallback to 'default-dev-key' if API_KEY is not in .env
    expected_key = os.getenv("API_KEY", "default-dev-key")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key

# Mount static files for the frontend
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    role: str
    content: str = None
    name: str = None
    args: dict = None
    response: dict = None

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok", "app": "AgentForge"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/chat")
@limiter.limit("20/minute")
async def chat_endpoint(req_body: ChatRequest, request: Request, api_key: str = Depends(get_api_key)):
    # Convert history into a serializable format for the loop if needed,
    # or just pass it straight in.
    history_dict = [{"role": msg.role, "content": msg.content, "name": getattr(msg, "name", None), "args": getattr(msg, "args", None), "response": getattr(msg, "response", None)} for msg in req_body.history]
    
    async def event_stream():
        for step in run_agent_loop(req_body.message, history=history_dict):
            if await request.is_disconnected():
                print("Client disconnected, stopping agent loop.")
                break
            yield f"data: {json.dumps(step)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
