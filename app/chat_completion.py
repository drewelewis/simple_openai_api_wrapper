import os
import ai.azure_openai_client as azure_openai_client

prompt = os.getenv("OPENAI_PROMPT", "You are a helpful assistant.")

def get(query: str) -> str:
    messages = [
        {"role": "system", "content": prompt}
    ]
    messages.append({"role": "user", "content": query})
    client = azure_openai_client.client()
    completion = client.completion(messages, max_tokens=10000)
    try:
        message=completion.choices[0].message.content
        return message
    except Exception as e:
        return "There was an issue with your request, please try again later"
    
def chat(messages: str) -> str:
    total_messages = [
        {"role": "system", "content": prompt}
    ]
    total_messages.append({"role": "user", "content": messages})
    client = azure_openai_client.client()
    completion = client.completion(total_messages, max_tokens=10000)
    try:
        message=completion.choices[0].message.content
        return message
    except Exception as e:
        return "There was an issue with your request, please try again later"