# FastAPI Inventory Service

REST API для учёта оборудования. Переписан с Flask на FastAPI для демонстрации типизации и автодокументации.

## Эндпоинты

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| GET | `/api/search` | query: `q`, `device_type`, `limit` | Универсальный поиск |
| GET | `/api/devices/{device_id}` | path: `device_id` | Получить устройство по ID |
| POST | `/api/disputes` | body: `device_id`, `reason`, `comment` | Создать оспаривание |
| POST | `/api/devices` | body: устройство | Добавить устройство |
| GET | `/api/devices` | query: `skip`, `limit` | Список с пагинацией |

## Требования задания

- ✅ 3+ ручки (реализовано 5)
- ✅ Query параметры (`/api/search?q=Y1000&device_type=computer`)
- ✅ Path параметры (`/api/devices/1`)
- ✅ Body параметры (POST `/api/disputes`)
- ✅ POST-запрос с демонстрацией
- ✅ Тесты (pytest + httpx, 8 тестов)
- ✅ Развёрнут на Render: https://fastapi-inventory.onrender.com

## Локальный запуск

```bash
pip install -r requirements.txt
uvicorn main:app --reload