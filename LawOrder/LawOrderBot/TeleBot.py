from telebot import types, TeleBot
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import datetime
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LawOrder.settings")


# Загрузка переменных окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("Не найден TOKEN в .env файле")

print(f'{datetime.datetime.now()} Загружен токен бота {TOKEN}')
bot = TeleBot(TOKEN)

# def COMPANYLOOKUP(input):
#     response=UrlFetchApp.fetch("https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn="+input).getContentText();
#     return response;

# def COMPANYLOOKUP(input):
#     url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
#     response = requests.get(url)
#     return response.text

def COMPANYLOOKUP(input):
    url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Ошибка запроса: {e}"

#Основное меню
@bot.message_handler(content_types=["text"])
def next_message(message):
    print(f"{datetime.datetime.now()} Получено сообщение: {message.text}")  # Логирование входящих сообщений
    #from news.models import TelegramSubscriber
    chat_id = message.chat.id
    username = message.from_user.username or "Неизвестный пользователь"
    if message.text.lower() == '/law_order':
        keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Подписаться на бота', callback_data='key1')
        button2 = types.InlineKeyboardButton('Отписаться от бота', callback_data='key2')
        button3 = types.InlineKeyboardButton('Запустить парсер', callback_data='key3')
        keyboard_subcategory.add(button1, button2, button3)

        bot.send_message(chat_id, 
                    text=f"Добро пожаловать, {username}!\nНомер чата: {chat_id}\nВыберите действие:",
                    reply_markup=keyboard_subcategory)            
    else:
        bot.send_message(message.chat.id, f"Недоступная операция: {message.text}")
        print(f"{datetime.datetime.now()} Недоступная операция: {message.text}")
#Основное меню2
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    django.setup()
    from LawOrderParser.models import TelegramSubscriber
    chat_id = call.message.chat.id
    username = call.from_user.username or "Неизвестный пользователь"
    if call.data == 'key0':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Подписаться на бота', callback_data='key1'),
                        types.InlineKeyboardButton('Отписаться от бота', callback_data='key2'))
        bot.edit_message_text('Выберите операцию', chat_id, call.message.message_id, reply_markup=keyboard_category)
    # Обработка подписки на бота
    elif call.data == 'key1':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'))
        
        subscriber, created = TelegramSubscriber.objects.get_or_create(
            chat_id=chat_id, 
            defaults={'username': username}
        )
        message_text = "Вы успешно подписались на бота как {subscriber}." if created else "Вы уже подписаны на бота как {subscriber}, подписка недоступна."
        bot.edit_message_text(message_text, chat_id, call.message.message_id, reply_markup=keyboard_category)

    # Обработка отписки от бота
    elif call.data == 'key2':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'))
        
        deleted_count, _ = TelegramSubscriber.objects.filter(chat_id=chat_id).delete()
        message_text = "Вы успешно отписались от бота." if deleted_count > 0 else "Вы не были подписаны на бота, отписка невозможна."
        bot.edit_message_text(message_text, chat_id, call.message.message_id, reply_markup=keyboard_category)

    # Обработка запуска парсера
    elif call.data == 'key3':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'))
        
        deleted_count, _ = TelegramSubscriber.objects.filter(chat_id=chat_id).delete()
        message_text = "Запуск парсера"
        bot.edit_message_text(message_text, chat_id, call.message.message_id, reply_markup=keyboard_category)


#запуск бота через supervisord
def run_bot():
    now = datetime.datetime.now()
    print(f"{now} Запуск Telegram-бота...")
    try:
        # Запуск polling с настройкой тайм-аутов
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        now = datetime.datetime.now()
        print(f"{now} Ошибка: {e}")
if __name__ == "__main__":
    run_bot()