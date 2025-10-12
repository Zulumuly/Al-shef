import requests
import os
from config import GIGACHAT_TOKEN

# Путь к корневому сертификату Минцифры РФ
CERT_PATH = os.path.join(os.path.dirname(__file__), "russian_trusted_root_ca_pem.crt")

def ask_gigachat(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GIGACHAT_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            json=data,
            headers=headers,
            verify=CERT_PATH,  # ✅ Указываем сертификат Минцифры
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.exceptions.SSLError as e:
        return f"⚠️ Ошибка SSL. Сертификат недоверенный. Проверь файл {CERT_PATH}."
    except Exception as e:
        return f"❌ Ошибка при обращении к GigaChat: {e}"
