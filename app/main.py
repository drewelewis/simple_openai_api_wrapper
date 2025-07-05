import re
from fastapi import FastAPI

from app import chat_completion

app = FastAPI()

@app.get("/")
async def root(query: str = "how are you?"):
    response=chat_completion.get(query)
    # message="hello world"
    return response

# chat with messages input
# get the messages from the request body
@app.post("/chat")
async def chat(messages: str):
    response=chat_completion.chat(messages)
    # message="hello world"
    return response
