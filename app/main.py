import re
from fastapi import FastAPI

from app import chat_completion

app = FastAPI()

@app.get("/")
async def root(query: str = "how are you?"):
    message=chat_completion.get(query)
    return message
    
