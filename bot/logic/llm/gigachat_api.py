import os
import uuid
import requests
from config import GIGACHAT_AUTH_KEY, GIGACHAT_SCOPE

# 🌐 Эндпоинты GigaChat
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
CERT_PATH = os.path.join(os.path.dirname(__file__), "russian_trusted_root_ca_pem.crt")

# 🧠 Кэш токена
ACCESS_TOKEN = None
TOKEN_EXPIRES = None


def get_access_token():
    """Запрашивает новый access_token для GigaChat API"""
    global ACCESS_TOKEN, TOKEN_EXPIRES

    headers = {
        "Authorization": GIGACHAT_AUTH_KEY,
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    data = {"scope": GIGACHAT_SCOPE}

    response = requests.post(
        AUTH_URL,
        headers=headers,
        data=data,
        verify=CERT_PATH,  # сертификат Минцифры
    )

    if response.status_code != 200:
        raise Exception(
            f"Ошибка получения токена: {response.status_code} {response.text}"
        )

    token_data = response.json()
    ACCESS_TOKEN = token_data["access_token"]
    TOKEN_EXPIRES = token_data.get("expires_at")
    print("✅ GigaChat access token obtained successfully")
    return ACCESS_TOKEN


def ask_gigachat(prompt: str) -> str:
    """Отправляет запрос в GigaChat"""
    token = ACCESS_TOKEN or get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(
        CHAT_URL,
        headers=headers,
        json=payload,
        verify=CERT_PATH,
    )

    # Если токен истёк — пробуем обновить
    if response.status_code == 401:
        print("⚠️ Токен истёк, запрашиваю новый...")
        token = get_access_token()
        headers["Authorization"] = f"Bearer {token}"
        response = requests.post(
            CHAT_URL,
            headers=headers,
            json=payload,
            verify=CERT_PATH,
        )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
