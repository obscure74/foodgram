# Foodgram — "Продуктовый помощник"

## Описание проекта

Foodgram — это веб-приложение для публикации и управления рецептами. Пользователи могут:
- Публиковать свои рецепты с фото, описанием, ингредиентами и временем приготовления
- Просматривать рецепты других авторов
- Подписываться на любимых авторов
- Добавлять рецепты в избранное и список покупок
- Автоматически формировать список продуктов для приготовления рецептов

## Ссылки

- **Работающий сайт:** http://178.154.212.234
- **Админка:** http://178.154.212.234/admin/
- **API документация:** http://178.154.212.234/api/docs/

## Docker образы

- **Backend:** https://hub.docker.com/r/obscure74/foodgram_backend
- **Frontend:** https://hub.docker.com/r/obscure74/foodgram_frontend

## Технологии

- **Backend:** Python 3.12, Django 5.1.3, Django REST Framework
- **Frontend:** React
- **База данных:** PostgreSQL 15
- **Контейнеризация:** Docker, Docker Compose
- **Веб-сервер:** Nginx
- **CI/CD:** GitHub Actions

## Установка и запуск

### Через Docker Compose (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/obscure74/foodgram.git
cd foodgram
```

2. Перейдите в папку `infra` и создайте файл `.env` с переменными окружения:
```bash
cd infra
nano .env
```

Пример содержимого `.env`:
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Важно:** файл `.env` не должен попасть в репозиторий. Он уже добавлен в `.gitignore`.

3. Запустите контейнеры:
```bash
docker compose up -d
```

При запуске контейнер `frontend` подготовит файлы для фронтенд-приложения и завершит работу. Контейнер `backend` автоматически применит миграции и соберёт статику.

4. Создайте суперпользователя:
```bash
docker compose exec backend python manage.py createsuperuser
```

5. Откройте сайт в браузере:
- Фронтенд: http://localhost
- API: http://localhost/api/
- API документация: http://localhost/api/docs/
- Админка: http://localhost/admin/

### Локальная разработка (без Docker)

1. Создайте виртуальное окружение и активируйте его:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. В файле `backend/foodgram/settings.py` база данных автоматически переключится на SQLite, если не заданы переменные окружения PostgreSQL.

4. Примените миграции:
```bash
python manage.py migrate
```

5. Загрузите ингредиенты:
```bash
python manage.py load_ingredients data/ingredients.json
```

6. Запустите сервер разработки:
```bash
python manage.py runserver
```

## CI/CD

Проект настроен с GitHub Actions. При push в ветку `main` автоматически:
1. Запускаются тесты (`tests.yml`)
2. Собираются Docker образы backend и frontend
3. Образы загружаются в Docker Hub
4. Происходит деплой на продакшен сервер через SSH

## Автор

**Ксения Будкина**
GitHub: [obscure74] (https://github.com/obscure74)
Email: obscure.74@yandex.ru
