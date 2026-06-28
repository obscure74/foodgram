import requests
import json
import random

BASE_URL = "http://178.154.212.234"
NO_PROXY = {'http': None, 'https': None}

class APITester:
    def __init__(self):
        self.token = None
        self.user_token = None
        self.second_user_token = None
        self.first_user_id = None
        self.second_user_id = None
        self.recipe_id = None
        self.results = {'passed': 0, 'failed': 0, 'errors': []}
    
    def log(self, test_name, status_code, expected, response=None):
        passed = status_code == expected
        if passed:
            self.results['passed'] += 1
            print(f"✅ {test_name}: {status_code} (ожидалось {expected})")
        else:
            self.results['failed'] += 1
            error_msg = f"❌ {test_name}: получено {status_code}, ожидалось {expected}"
            if response and response.text:
                try:
                    error_msg += f"\n   Ответ: {json.dumps(response.json(), ensure_ascii=False)[:200]}"
                except Exception:
                    error_msg += f"\n   Ответ: {response.text[:200]}"
            self.results['errors'].append(error_msg)
            print(error_msg)
    
    def get_headers(self, token=None):
        if token:
            return {"Authorization": f"Token {token}"}
        return {}
    
    def test_registration(self):
        print("\n" + "="*60)
        print("🔍 ТЕСТЫ РЕГИСТРАЦИИ")
        print("="*60)
        
        # Тест 1: Регистрация с некорректным username
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
        self.log("user_registration_with_invalid_username", response.status_code, 400, response)
        
        # Генерируем уникальные данные для пользователей
        rand_id = random.randint(1, 100000)
        self.first_user_email = f"vivanov_{rand_id}@yandex.ru"
        self.first_username = f"vasya.ivanov_{rand_id}"
        
        # Тест 2: Регистрация первого пользователя
        response = requests.post(
            f"{BASE_URL}/api/users/",
            json={
                "username": self.first_username,
                "email": self.first_user_email,
                "first_name": "Вася",
                "last_name": "Иванов",
                "password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        self.log("create_first_user", response.status_code, 201, response)
        if response.status_code == 201:
            self.first_user_id = response.json().get("id")
        
        # Тест 3: Регистрация второго пользователя
        self.second_user_email = f"second_user_{rand_id}@email.org"
        self.second_username = f"second-user_{rand_id}"
        response = requests.post(
            f"{BASE_URL}/api/users/",
            json={
                "username": self.second_username,
                "email": self.second_user_email,
                "first_name": "Андрей",
                "last_name": "Макаревский",
                "password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        self.log("create_second_user", response.status_code, 201, response)
        # Сохраняем ID второго пользователя для теста отписки
        if response.status_code == 201:
            self.second_user_id = response.json().get("id")
        else:
            self.second_user_id = None
    
    def test_authentication(self):
        print("\n" + "="*60)
        print("🔍 ТЕСТЫ АУТЕНТИФИКАЦИИ")
        print("="*60)
        
        # Получение токена первого пользователя
        response = requests.post(
            f"{BASE_URL}/api/auth/token/login/",
            json={
                "email": self.first_user_email,
                "password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        self.log("get_user_token", response.status_code, 200, response)
        if response.status_code == 200:
            self.user_token = response.json().get("auth_token")
        
        # Получение токена второго пользователя
        response = requests.post(
            f"{BASE_URL}/api/auth/token/login/",
            json={
                "email": self.second_user_email,
                "password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        self.log("get_second_user_token", response.status_code, 200, response)
        if response.status_code == 200:
            self.second_user_token = response.json().get("auth_token")
    
    def test_users(self):
        print("\n" + "="*60)
        print("🔍 ТЕСТЫ ПОЛЬЗОВАТЕЛЕЙ")
        print("="*60)
        
        headers = self.get_headers(self.user_token)
        
        # GET /api/users/?limit=2
        response = requests.get(f"{BASE_URL}/api/users/?limit=2", headers=headers, proxies=NO_PROXY)
        self.log("get_user_list_with_limit_param", response.status_code, 200, response)
        
        # GET /api/users/me/
        response = requests.get(f"{BASE_URL}/api/users/me/", headers=headers, proxies=NO_PROXY)
        self.log("get_current_user_me", response.status_code, 200, response)
        
        # PUT /api/users/me/avatar/
        response = requests.put(
            f"{BASE_URL}/api/users/me/avatar/",
            headers=headers,
            json={"avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="},
            proxies=NO_PROXY
        )
        self.log("set_avatar", response.status_code, 200, response)
        
        # Проверка аватара
        response = requests.get(f"{BASE_URL}/api/users/me/", headers=headers, proxies=NO_PROXY)
        self.log("check_avatar_is_set", response.status_code, 200, response)
        if response.status_code == 200:
            avatar = response.json().get("avatar")
            if avatar:
                self.results['passed'] += 1
                print("✅ Поле avatar содержит ссылку")
            else:
                self.results['failed'] += 1
                print("❌ Поле avatar не содержит ссылку (null или пусто)")
    
    def test_password_change(self):
        print("\n" + "="*60)
        print("🔍 ТЕСТЫ СМЕНЫ ПАРОЛЯ")
        print("="*60)
        
        headers = self.get_headers(self.user_token)
        
        # Смена пароля
        response = requests.post(
            f"{BASE_URL}/api/users/set_password/",
            headers=headers,
            json={
                "current_password": "MySecretPas$word",
                "new_password": "NewPassword123!"
            },
            proxies=NO_PROXY
        )
        self.log("reset_password", response.status_code, 204, response)
        
        # Получение токена с новым паролем
        response = requests.post(
            f"{BASE_URL}/api/auth/token/login/",
            json={
                "email": self.first_user_email,
                "password": "NewPassword123!"
            },
            proxies=NO_PROXY
        )
        self.log("get_token_with_new_password", response.status_code, 200, response)
        if response.status_code == 200:
            self.user_token = response.json().get("auth_token")
            headers = self.get_headers(self.user_token)
        
        # Возврат старого пароля
        response = requests.post(
            f"{BASE_URL}/api/users/set_password/",
            headers=headers,
            json={
                "current_password": "NewPassword123!",
                "new_password": "MySecretPas$word"
            },
            proxies=NO_PROXY
        )
        self.log("roll_back_password", response.status_code, 204, response)
    
    def test_subscriptions(self):
        print("\n" + "="*60)
        print("🔍 ТЕСТЫ ПОДПИСОК")
        print("="*60)
        
        headers = self.get_headers(self.user_token)
        
        if getattr(self, 'second_user_id', None):
            # Удаление несуществующей подписки на СУЩЕСТВУЮЩЕГО пользователя
            # Ожидаем 400 Bad Request, так как подписки между ними еще нет
            response = requests.delete(
                f"{BASE_URL}/api/users/{self.second_user_id}/subscribe/",
                headers=headers,
                proxies=NO_PROXY
            )
            self.log("delete_non_existing_subscription", response.status_code, 400, response)
        else:
            print("⚠️ Пропуск теста отписки: второй пользователь не был создан.")
    
    def run_all_tests(self):
        print("\n" + "="*60)
        print("🚀 НАЧАЛО ПОЛНОГО ТЕСТИРОВАНИЯ API")
        print("="*60)
        
        self.test_registration()
        self.test_authentication()
        self.test_users()
        self.test_password_change()
        self.test_subscriptions()
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("="*60)
        print(f"✅ Пройдено: {self.results['passed']}")
        print(f"❌ Провалено: {self.results['failed']}")
        
        if self.results['errors']:
            print("\n❌ ДЕТАЛИ ПРОВАЛЕННЫХ ТЕСТОВ:")
            for error in self.results['errors']:
                print(error)
        
        return self.results

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
