# import sys
# sys.path.append('/yt')
import os
from django.conf import settings
import time
from celery import shared_task
# from LawOrderParser.task.sudact_parsing import sudact_find
from celery.utils.log import get_task_logger
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawOrder.settings')
import django

# для редиски
import uuid
import redis
from LawOrderParser.utils.redis_client import redis_client
# from LawOrderParser.task.sudact_parsing import parse_document
from LawOrderParser.task.sudact_parsing_doc import parse_document

# Подключение к Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

django.setup()
logger = get_task_logger(__name__)
# load_dotenv()
# TOKEN = os.getenv("TOKEN")

# Пример функции для сохранения ссылки
def save_temp_link(key, url, ttl_seconds=300):
    r.setex(key, ttl_seconds, url)
    print(f"Ссылка сохранена: {key} → {url} (на {ttl_seconds} сек)")

# Пример функции для получения ссылки
def get_temp_link(key):
    url = r.get(key)
    if url:
        print(f"Ссылка получена: {key} → {url}")
    else:
        print(f"Ссылка по ключу {key} не найдена или истекла")
    return url

@shared_task(bind=True)
def parsing(self, mode="manual"):
    #сценарий ручного запуска парсинга
    from LawOrderParser.task.sudact_parsing import sudact_find
    import uuid
    try:
        result_message, parsed_items = sudact_find(mode=mode)
        if not parsed_items:
            print("парсер не нашел данные")
            return {"ok": False, "message": result_message or "❌ Ничего не найдено."}
        
        # Создаём список пар: (текст кнопки, redis_key)
        buttons = []
        for item in parsed_items:
            button_text = f"№{item['number']}: {item['title'][:50]}"
            redis_key = f"doc_link:{uuid.uuid4()}"
            redis_client.setex(redis_key, 1800, item['url'])  # TTL 5 минут
            print(f"подготовлена кнопка {button_text}, {redis_key}")
            buttons.append((button_text, redis_key))

        print("Возвращаем результат в parsing:", {
            "ok": True,
            "message": "...",
            "buttons": buttons
        })
        
        return {
            "ok": True,
            "message": "✅ Парсинг завершён. Выберите документ для анализа:",
            "buttons": buttons
        }
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {str(e)}")
        return {"ok": False, "message": f"❌ Ошибка при парсинге: {str(e)}"}

@shared_task(bind=True)
def test_read_redis_key(self, redis_key):
    try:
        print(f"🧪 Получен ключ: {redis_key}")
        value = redis_client.get(redis_key)

        if value is None:
            print(f"❌ Ключ {redis_key} не найден или устарел.")
            return {"ok": False, "message": f"❌ Ключ {redis_key} не найден в Redis."}

        decoded_value = value.decode() if isinstance(value, bytes) else value
        print(f"✅ Значение по ключу: {decoded_value}")
        return {"ok": True, "url": decoded_value, "redis_key": redis_key}

    except Exception as e:
        print(f"❌ Ошибка в тестовой задаче: {str(e)}")
        return {"ok": False, "message": f"❌ Ошибка: {str(e)}"}

# @shared_task(bind=True)
# def parsing_doc_task(self, redis_key, mode="manual"):
#     try:
#         print(f"🧪 Получен ключ: {redis_key}")
#         value = redis_client.get(redis_key)

#         if value is None:
#             print(f"❌ Ключ {redis_key} не найден или устарел.")
#             return {"ok": False, "message": f"❌ Ключ {redis_key} не найден в Redis."}
#         decoded_value = value.decode() if isinstance(value, bytes) else value
#         # запускаем парсинг документа
#         document = parse_document(decoded_value, mode=mode)
        
#         return "doc"
#     except Exception as e:
#         print(f"❌ Ошибка в тестовой задаче: {str(e)}")
#         return {"ok": False, "message": f"❌ Ошибка: {str(e)}"}

@shared_task(bind=True)
def parsing_doc_task(self, redis_key, mode="manual"):
    try:
        result = parse_document(redis_key, mode=mode)
        return result
    except Exception as e:
        return {"ok": False, "message": f"❌ Ошибка: {str(e)}"}
