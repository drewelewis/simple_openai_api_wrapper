import re
from fastapi import FastAPI, Response
from openai import APIError, RateLimitError, AuthenticationError, APIConnectionError, InternalServerError
import ai.azure_openai_client as azure_openai_client

from app import chat_completion
from agents import agent_bing_grounding
from models.model import Messages

app = FastAPI()

# Create input model for chat messages
from pydantic import BaseModel, Field


@app.get("/health")
async def health_check(response: Response):
    """
    Health check endpoint that verifies Azure OpenAI connectivity.
    Returns appropriate HTTP status codes based on Azure OpenAI response.
    """
    try:
        # Make a minimal test call to Azure OpenAI
        client = azure_openai_client.client()
        test_messages = [{"role": "user", "content": "test"}]
        client.completion(test_messages, max_tokens=1)
        
        return {"status": "ok", "azure_openai": "connected"}
    
    except AuthenticationError as e:
        # 401 - Authentication failed
        response.status_code = 401
        return {
            "status": "error",
            "error": "authentication_error",
            "message": "Azure OpenAI authentication failed",
            "details": str(e)
        }
    
    except RateLimitError as e:
        # 429 - Rate limit exceeded
        response.status_code = 429
        return {
            "status": "error",
            "error": "rate_limit_exceeded",
            "message": "Azure OpenAI rate limit exceeded",
            "details": str(e)
        }
    
    except InternalServerError as e:
        # 503 - Service unavailable
        response.status_code = 503
        return {
            "status": "error",
            "error": "service_unavailable",
            "message": "Azure OpenAI service unavailable",
            "details": str(e)
        }
    
    except APIConnectionError as e:
        # 503 - Connection error
        response.status_code = 503
        return {
            "status": "error",
            "error": "connection_error",
            "message": "Failed to connect to Azure OpenAI",
            "details": str(e)
        }
    
    except APIError as e:
        # Generic API error - use status code from the error if available
        response.status_code = e.status_code if hasattr(e, 'status_code') else 500
        return {
            "status": "error",
            "error": "api_error",
            "message": "Azure OpenAI API error",
            "details": str(e)
        }
    
    except Exception as e:
        # Catch-all for unexpected errors
        response.status_code = 500
        return {
            "status": "error",
            "error": "internal_error",
            "message": "Unexpected error during health check",
            "details": str(e)
        }

@app.get("/completion")
async def completion(query: str = "how are you?"):
    response=chat_completion.completion(query)
    return response

@app.post("/chat")
async def chat(messages: Messages):
    message=chat_completion.chat(messages.messages)
    return message

@app.post("/bing-grounding")
async def bing_grounding(query: str):
    """Endpoint for Bing grounding agent chat with citations"""
    import json
    response = agent_bing_grounding.chat(query)
    # Parse the JSON string and return as dict for proper JSON response
    return json.loads(response)