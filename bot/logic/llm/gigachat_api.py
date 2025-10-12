import requests
import os
import json

CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


def get_access_token():
    headers = {
        "Authorization": f"Basic {requests.utils.quote(f'{CLIENT_ID}:{CLIENT_SECRET}')}",
        "RqUID": "12345678-1234-1234-1234-123456789012",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False)

    if response.status_code != 200:
        raise Exception(f"Ошибка получения токена: {response.status_code}, {response.text}")

    token_data = response.json()
    return token_data.get("access_token")


def ask_gigachat(prompt: str) -> str:
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "GigaChat:latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 800
        }

        response = requests.post(CHAT_URL, headers=headers, json=payload, timeout=60, verify=False)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"❌ Ошибка при обращении к GigaChat: {e}")
        return "Ошибка при обращении к GigaChat 😞"
