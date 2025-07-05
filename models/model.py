from pydantic import BaseModel
from pydantic import Field

class ai_response(BaseModel):
    text: str
    errors: str

class article(BaseModel):
    url: str
    title: str
    text: str
    text_embedding: list[float]
    text_token_count: int


class Message(BaseModel):
    role: str = Field(..., description="Type of the message, e.g., 'user' or 'assistant' or 'system'")
    content: str = Field(..., description="Content of the message")

class Messages(BaseModel):
    messages: list[Message] = Field(..., description="List of messages in the chat")