import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from model import Message
from bot import chat
from database import init_db, get_all_leads

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="TedRed Support Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="widget"), name="static")

@app.get("/widget")
async def serve_widget():
    return FileResponse("widget/chat-widget.html")

@app.api_route("/", methods=["GET", "HEAD", "POST"])
async def root():
    return {"status": "TedRed bot is live"}

@app.post("/chat")
async def chat_endpoint(msg: Message):
    reply = await chat(msg.session_id, msg.message)
    print(f"DEBUG: Sending reply: {reply}")
    return JSONResponse(content={"reply": reply})

@app.get("/leads")
async def get_leads():
    leads = await get_all_leads()
    return {"leads": leads, "total": len(leads)}