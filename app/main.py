import re
from fastapi import FastAPI

from app import chat_completion
from models.model import Messages

app = FastAPI()

# Create input model for chat messages
from pydantic import BaseModel, Field


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/completion")
async def completion(query: str = "how are you?"):
    response=chat_completion.completion(query)
    return response

@app.post("/chat")
async def chat(messages: Messages):
    message=chat_completion.chat(messages.messages)
    return message
