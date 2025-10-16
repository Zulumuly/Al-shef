import requests
import os
import base64

CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise Exception("Отсутствуют GIGACHAT_CLIENT_ID или GIGACHAT_CLIENT_SECRET в переменных окружения")

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "RqUID": "12345678-1234-1234-1234-123456789012",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"scope": "GIGACHAT_API_PERS"}

    response = requests.post(TOKEN_URL, headers=headers, data=data, verify=False)

    if response.status_code != 200:
        print(f"Ошибка получения токена: {response.status_code}, {response.text}")
        raise Exception(f"Ошибка получения токена: {response.status_code}, {response.text}")

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise Exception(f"Не удалось получить access_token. Ответ: {token_data}")

    print("Токен успешно получен")
    return access_token


def ask_gigachat(prompt: str) -> str:
    """Отправляет запрос к GigaChat и получает ответ"""
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
            "max_tokens": 800,
        }

        response = requests.post(CHAT_URL, headers=headers, json=payload, timeout=60, verify=False)
        response.raise_for_status()

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        print("Ответ от GigaChat получен успешно")
        return answer

    except Exception as e:
        print(f"Ошибка при обращении к GigaChat: {e}")
        if "response" in locals():
            print("Ответ сервера:", response.text)
        return "Ошибка при обращении к GigaChat"
