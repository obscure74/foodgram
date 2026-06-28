import requests
import json

BASE_URL = "http://178.154.212.234"

def print_response(response, test_name):
    print(f"\n{'='*60}")
    print(f"ТЕСТ: {test_name}")
    print(f"URL: {response.url}")
    print(f"Метод: {response.request.method}")
    print(f"Статус: {response.status_code}")
    try:
        print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Ответ: {response.text[:500]}")
    print(f"{'='*60}\n")

# Отключаем прокси для всех запросов
NO_PROXY = {'http': None, 'https': None}

# Тест 1: Регистрация с некорректным username
print("\n🔍 ТЕСТ 1: Регистрация с некорректным username")
response = requests.post(
    f"{BASE_URL}/api/users/", 
    json={
        "username": "InvalidU$ername",
        "email": "invalid-username@test.ru",
        "first_name": "Invalid",
        "last_name": "Username",
        "password": "MySecretPas$word"
    },
    proxies=NO_PROXY  # ← ВАЖНО!
)
print_response(response, "Регистрация с некорректным username (должен быть 400)")
# Тест 2: Получение токена
print("\n ТЕСТ 2: Получение токена")
response = requests.post(f"{BASE_URL}/api/auth/token/login/", json={
    "email": "vivanov@yandex.ru",
    "password": "MySecretPas$word"
})
print_response(response, "Получение токена (должен быть 200)")

if response.status_code == 200:
    token = response.json().get("auth_token")
    headers = {"Authorization": f"Token {token}"}
    
    # Тест 3: Получение профиля текущего пользователя
    print("\n ТЕСТ 3: GET /api/users/me/")
    response = requests.get(f"{BASE_URL}/api/users/me/", headers=headers)
    print_response(response, "Получение профиля (должен быть 200, поле avatar)")
    
    # Тест 4: Установка аватара
    print("\n ТЕСТ 4: PUT /api/users/me/avatar/")
    response = requests.put(f"{BASE_URL}/api/users/me/avatar/", 
        headers=headers,
        json={"avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="}
    )
    print_response(response, "Установка аватара (должен быть 200)")
    
    # Тест 5: Смена пароля
    print("\n ТЕСТ 5: POST /api/users/set_password/")
    response = requests.post(f"{BASE_URL}/api/users/set_password/",
        headers=headers,
        json={
            "current_password": "MySecretPas$word",
            "new_password": "NewPassword123!"
        }
    )
    print_response(response, "Смена пароля (должен быть 204)")
    
    # Тест 6: Получение токена с новым паролем
    print("\n ТЕСТ 6: Получение токена с новым паролем")
    response = requests.post(f"{BASE_URL}/api/auth/token/login/", json={
        "email": "vivanov@yandex.ru",
        "password": "NewPassword123!"
    })
    print_response(response, "Получение токена с новым паролем (должен быть 200)")
    
    # Возвращаем старый пароль
    if response.status_code == 200:
        new_token = response.json().get("auth_token")
        headers = {"Authorization": f"Token {new_token}"}
        requests.post(f"{BASE_URL}/api/users/set_password/",
            headers=headers,
            json={
                "current_password": "NewPassword123!",
                "new_password": "MySecretPas$word"
            }
        )

print("\n Все тесты завершены!")