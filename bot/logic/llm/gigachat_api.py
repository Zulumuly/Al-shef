import requests
from bot.config import GIGACHAT_TOKEN

def ask_gigachat(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json=data,
        headers=headers,
        timeout=60
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
