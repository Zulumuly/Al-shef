import os
import uuid
import requests
import base64
import time

CERT_PATH = os.path.join(os.path.dirname(__file__), "sber.pem")

CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

TOKEN_CACHE = {"token": None, "expires": 0}


def get_access_token():
    """Получаем access token через OAuth2"""
    now = time.time()
    if TOKEN_CACHE["token"] and now < TOKEN_CACHE["expires"]:
        return TOKEN_CACHE["token"]

    auth_key = f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")
    auth_b64 = base64.b64encode(auth_key).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_b64}",
    }

    data = {"scope": "GIGACHAT_API_PERS"}

    response = requests.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        headers=headers,
        data=data,
        verify=CERT_PATH,
    )

    if response.status_code != 200:
        raise Exception(f"Ошибка получения токена: {response.text}")

    token_data = response.json()
    TOKEN_CACHE["token"] = token_data["access_token"]
    TOKEN_CACHE["expires"] = now + 1700
    return TOKEN_CACHE["token"]


def ask_gigachat(prompt: str):
    """Отправка запроса в GigaChat"""
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        headers=headers,
        json=payload,
        verify=CERT_PATH,
    )

    if response.status_code != 200:
        raise Exception(f"Ошибка при обращении к GigaChat: {response.status_code} {response.text}")

    return response.json()["choices"][0]["message"]["content"]
