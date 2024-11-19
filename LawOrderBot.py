from telebot import types, TeleBot
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
now = datetime.datetime.now()
print(f'{now} Загружен токен бота {TOKEN}')
bot = TeleBot(TOKEN)

# def COMPANYLOOKUP(input):
#     response=UrlFetchApp.fetch("https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn="+input).getContentText();
#     return response;

def COMPANYLOOKUP(input):
    url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
    response = requests.get(url)
    return response.text


#Основное меню
@bot.message_handler(content_types=["text"])
def next_message(message):
    now = datetime.datetime.now()
    print(f"{now} Получено сообщение: {message.text}")  # Логирование входящих сообщений
    #from news.models import TelegramSubscriber
    chat_id = message.chat.id
    username = message.from_user.username
    if message.text.lower() == '/law_order':
        keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1')
        button2 = types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2')
        keyboard_subcategory.add(button1, button2)

        # subscriber, created = TelegramSubscriber.objects.get_or_create(
        #     chat_id=chat_id,
        #     defaults={'username': username}
        # )
        # if created:
        #     bot.send_message(chat_id, 
        #     text=f"Добро пожаловать, {username}!\nВыберите действие:")
        # else:
        #     bot.send_message(chat_id, 
        #     text=f"Добро день, {username}!\nВыберите действие:")

        # bot.send_message(chat_id, 
        #     text=f"Добро пожаловать, {username}!\nВыберите действие:")

        bot.send_message(chat_id, 
                    text=f"Добро пожаловать, {username}!\nВыберите действие:",
                    reply_markup=keyboard_subcategory)
    #обработка инн
    # if message.text == "проверка кода ИНН":

    #     keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
    #     button1 = types.InlineKeyboardButton('Назад', callback_data='key0')
    #     keyboard_subcategory.add(button1)
    #     bot.send_message(chat_id, 
    #         text=f"Результат запроса\n{Выберите действие:}",
    #         reply_markup=keyboard_subcategory)

    # Новая проверка для сообщений, начинающихся с "ИНН:"
    elif message.text.startswith("ИНН:"):
        inn_id = message.text.split(":")[1].strip()  # Извлекаем ИНН после "ИНН:"
        if inn_id.isdigit() and len(inn_id) in [10, 12]:  # Проверяем длину и цифровой формат
            inn_request = COMPANYLOOKUP(inn_id)
            keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
            button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
            keyboard_subcategory.add(button_back)
            bot.send_message(chat_id, f"Получены данные по ИНН {inn_id}:\n{inn_request}", reply_markup=keyboard_subcategory)
        else:
            bot.send_message(chat_id, "Пожалуйста, введите корректный 10- или 12-значный ИНН.", reply_markup=keyboard_subcategory)

    elif message.text.isdigit() and len(message.text) in [10, 12]:
            inn_id = message.text
            inn_request = COMPANYLOOKUP(inn_id)
            #bot.send_message(chat_id, f"Получены данные по ИНН {inn_id}:\n{inn_request}")
            keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
            button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
            keyboard_subcategory.add(button_back)
            bot.send_message(chat_id, f"Получены данные по ИНН {inn_id}:\n{inn_request}", reply_markup=keyboard_subcategory)
            
    else:
        bot.send_message(message.chat.id, f"Недоступная операция: {message.text}")
        now = datetime.datetime.now()
        print(f"Недоступная операция: {message.text}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'key0':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1'),
                types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2'))
        bot.edit_message_text('Выберите операцию', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
    elif call.data == 'key1':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text('Введите запрос в формате ИНН:', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
    elif call.data == 'key2':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text('СШК еще не готово', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
    elif call.data.startswith('ИНН:'):
        inn_id = call.data.split(':')[1]
        now = datetime.datetime.now()
        print(f"{now} Получен ИНН:{inn_id}")
        inn_request = COMPANYLOOKUP(inn_id)
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text(f'Получены данные по ИНН:{inn_id} \n{inn_request}', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
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