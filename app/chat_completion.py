import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("_OPENAI_API_KEY"),  
    api_version=os.getenv("_OPENAI_API_VERSION"),
    azure_endpoint = os.getenv("_OPENAI_API_BASE")
    
)

def get(query: str) -> str:

    response = client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
            {"role": "user", "content": query}
        ],
    )

    try:
        return response.choices[0].message.content
    except Exception as e:
        return "There was an issue with your request, please try again later"
    

