import os
import ai.azure_openai_client as azure_openai_client
from models.model import Messages, Message



def completion(query: str) -> str:
    messages=[]
    # add system message to top to the messages list
    prompt = os.getenv("OPENAI_PROMPT", "You are a helpful assistant.")
    messages.insert(0, Message(role="system", content=prompt))
    messages.append(Message(role="user", content=query))

    client = azure_openai_client.client()
    completion = client.completion(messages, max_tokens=10000)
    try:
        message=completion.choices[0].message.content
        return message      
    except Exception as e:
        return "There was an issue with your request, please try again later"


def chat(messages: list[Message]) -> str:
    if messages[0].role != "system":
    # add system message to top to the messages list
        prompt = os.getenv("OPENAI_PROMPT", "You are a helpful assistant.")
        messages.insert(0, Message(role="system", content=prompt))

    client = azure_openai_client.client()
    completion = client.completion(messages=messages, max_tokens=10000)
    try:
        message=completion.choices[0].message.content
        # ai_message = Message(role="assistant", content=message)
        # messages.append(ai_message)
        return message
    except Exception as e:
        return "There was an issue with your request, please try again later"