import httpx
import logging
from database import Database

# Fallback constants in case DB is empty
from config import (
    OPENROUTER_API_KEY as FALLBACK_OPENROUTER_KEY,
    DASHSCOPE_API_KEY as FALLBACK_DASHSCOPE_KEY,
    AI_MODEL as FALLBACK_MODEL,
    AI_SYSTEM_PROMPT as FALLBACK_PROMPT,
    AI_PROVIDER as FALLBACK_PROVIDER
)

logger = logging.getLogger(__name__)
db = Database()

async def get_ai_response(chat_history):
    """
    Sends chat history to the configured AI provider and returns the AI response.
    Settings are fetched from the database with hardcoded fallbacks in config.py.
    """
    
    provider = db.get_setting('ai_provider', FALLBACK_PROVIDER)
    model = db.get_setting('ai_model', FALLBACK_MODEL)
    system_prompt = db.get_setting('ai_system_prompt', FALLBACK_PROMPT)
    
    if provider == "dashscope":
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        api_key = db.get_setting('dashscope_api_key', FALLBACK_DASHSCOPE_KEY)
    else: # Default to OpenRouter
        url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = db.get_setting('openrouter_api_key', FALLBACK_OPENROUTER_KEY)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # OpenRouter specific headers
    if provider == "openrouter":
        headers.update({
            "HTTP-Referer": "https://github.com/OpenRouter/rchatbotpy",
            "X-Title": "Telegram Random Chat Bot",
        })
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    
    payload = {
        "model": model,
        "messages": messages
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"{provider.title()} unexpected response: {data}")
                return "Sorry, I'm a bit busy right now. Can we talk later?"
                
    except Exception as e:
        logger.error(f"Error calling {provider.title()} API: {e}")
        return "Hey, sorry, my connection is acting up. One sec!"
