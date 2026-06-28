import requests
import json

BASE_URL = "http://178.154.212.234"
NO_PROXY = {'http': None, 'https': None}

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

print("\n" + "="*60)
print(" НАЧАЛО ТЕСТИРОВАНИЯ ВСЕХ ПРОБЛЕМНЫХ ЭНДПОИНТОВ")
print("="*60)

# Тест 1: Регистрация с некорректным username
print("\n ТЕСТ 1: Регистрация с некорректным username (должен быть 400)")
response = requests.post(
    f"{BASE_URL}/api/users/", 
    json={
        "username": "InvalidU$ername",
        "email": "invalid-username@test.ru",
        "first_name": "Invalid",
        "last_name": "Username",
        "password": "MySecretPas$word"
    },
    proxies=NO_PROXY
)
print_response(response, "Регистрация с некорректным username")

# Тест 2: Получение токена
print("\n ТЕСТ 2: Получение токена (должен быть 200)")
response = requests.post(
    f"{BASE_URL}/api/auth/token/login/", 
    json={
        "email": "vivanov@yandex.ru",
        "password": "MySecretPas$word"
    },
    proxies=NO_PROXY
)
print_response(response, "Получение токена")

if response.status_code == 200:
    token = response.json().get("auth_token")
    headers = {"Authorization": f"Token {token}"}
    
    # Тест 3: Получение списка пользователей с параметром limit
    print("\n ТЕСТ 3: GET /api/users/?limit=2 (должен быть 200, пагинация)")
    response = requests.get(
        f"{BASE_URL}/api/users/?limit=2",
        headers=headers,
        proxies=NO_PROXY
    )
    print_response(response, "Список пользователей с limit=2")
    
    # Тест 4: Получение профиля текущего пользователя
    print("\n ТЕСТ 4: GET /api/users/me/ (должен быть 200, поле avatar)")
    response = requests.get(
        f"{BASE_URL}/api/users/me/",
        headers=headers,
        proxies=NO_PROXY
    )
    print_response(response, "Получение профиля")
    
    # Тест 5: Установка аватара
    print("\n ТЕСТ 5: PUT /api/users/me/avatar/ (должен быть 200)")
    response = requests.put(
        f"{BASE_URL}/api/users/me/avatar/", 
        headers=headers,
        json={"avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="},
        proxies=NO_PROXY
    )
    print_response(response, "Установка аватара")
    
    # Тест 6: Проверка, что аватар установлен
    print("\n ТЕСТ 6: GET /api/users/me/ (должен быть 200, avatar не null)")
    response = requests.get(
        f"{BASE_URL}/api/users/me/",
        headers=headers,
        proxies=NO_PROXY
    )
    print_response(response, "Проверка аватара")
    
    # Тест 7: Смена пароля
    print("\n ТЕСТ 7: POST /api/users/set_password/ (должен быть 204)")
    response = requests.post(
        f"{BASE_URL}/api/users/set_password/",
        headers=headers,
        json={
            "current_password": "MySecretPas$word",
            "new_password": "NewPassword123!"
        },
        proxies=NO_PROXY
    )
    print_response(response, "Смена пароля")
    
    # Тест 8: Получение токена с новым паролем
    print("\n ТЕСТ 8: Получение токена с новым паролем (должен быть 200)")
    response = requests.post(
        f"{BASE_URL}/api/auth/token/login/", 
        json={
            "email": "vivanov@yandex.ru",
            "password": "NewPassword123!"
        },
        proxies=NO_PROXY
    )
    print_response(response, "Получение токена с новым паролем")
    
    if response.status_code == 200:
        new_token = response.json().get("auth_token")
        headers = {"Authorization": f"Token {new_token}"}
        
        # Тест 9: Возврат старого пароля
        print("\n ТЕСТ 9: POST /api/users/set_password/ (возврат старого пароля)")
        response = requests.post(
            f"{BASE_URL}/api/users/set_password/",
            headers=headers,
            json={
                "current_password": "NewPassword123!",
                "new_password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        print_response(response, "Возврат старого пароля")
        
        # Тест 10: Удаление несуществующей подписки
        print("\n ТЕСТ 10: DELETE /api/users/999/subscribe/ (должен быть 400 или 404)")
        response = requests.delete(
            f"{BASE_URL}/api/users/999/subscribe/",
            headers=headers,
            proxies=NO_PROXY
        )
        print_response(response, "Удаление несуществующей подписки")

print("\n Все тесты завершены!")