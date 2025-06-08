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
import time
from LawOrderParser.utils.redis_client import redis_client
from LawOrderParser.task.sudact_parsing import parse_document


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

# @shared_task
# def parsing():
#     logger.info("Начало выполнения задачи parsing")
#     try:
#         sudact_find()
#         logger.info("Задача parsing выполнена успешно")
#     except Exception as e:
#         logger.error(f"Ошибка выполнения задачи parsing: {e}")
#         raise

# @shared_task(bind=True)
# def parsing(self, mode="manual", chat_id=None, message_id=None):
#     from LawOrderParser.task.sudact_parsing import sudact_find
#     from telebot import types, TeleBot

#     # переделать указание токена через env файл
#     bot = TeleBot("7300227909:AAFLLNA14mxVCk5RvjP-LHc05yDO7dANKj4")

#     # Подготовим клавиатуру заранее
#     keyboard_category = types.InlineKeyboardMarkup(row_width=1)
#     keyboard_category.add(
#         types.InlineKeyboardButton('Запустить парсер', callback_data='key3'),
#         types.InlineKeyboardButton('Назад', callback_data='key0'))

#     message_text = "❌ Неизвестная ошибка."
    
#     try:
#         logger.info(f"Целевая задача parsing запущена. mode={mode}")
#         result, parsed_items = sudact_find(mode=mode)
#         # исключение когда нет данных страницы поиска
#         if not parsed_items:
#             message_text = "❌ Ничего не найдено."
#             return

#         # message_text = f"✅ Парсинг завершен:\n\n{result}"
#         message_text = f"✅ Парсинг завершен:\n\n Выберите документ для анализа"
#         #добавим кнопки с ссылками
#         for item in parsed_items:
#             button_text = f"№{item['number']}: {item['title'][:50]}"
#             # Сохраняем ссылку в Redis
#             key = f"doc_link:{uuid.uuid4()}"
#             redis_client.setex(key, 300, item['url'])  # TTL 5 минут
#             # по слову open_link будем ловить телеботом ссылки для парсинга конечных страниц
#             # callback_data = f"open_link:{key}"
#             keyboard_category.add(
#                 types.InlineKeyboardButton(button_text, callback_data=key))

#     except Exception as e:
#         logger.error(f"Ошибка: {e}")
#         message_text = f"❌ Ошибка при парсинге:\n{e}"
#         raise

#     if chat_id and message_id:
#         bot.edit_message_text(
#             message_text,
#             chat_id,
#             message_id,
#             reply_markup=keyboard_category
#         )

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