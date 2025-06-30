from pydantic import BaseModel

class ai_response(BaseModel):
    text: str
    errors: str

class article(BaseModel):
    url: str
    title: str
    text: str
    text_embedding: list[float]
    text_token_count: int