import os
import ai.azure_openai_client as azure_openai_client



def get(query: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    messages.append({"role": "user", "content": query})
    client = azure_openai_client.client()
    completion = client.completion(messages, max_tokens=10000)
    try:
        message=completion.choices[0].message.content
        return message
    except Exception as e:
        return "There was an issue with your request, please try again later"
    
