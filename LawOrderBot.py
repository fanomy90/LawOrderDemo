from telebot import types, TeleBot
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import urllib3
from bs4 import BeautifulSoup
import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
now = datetime.datetime.now()
print(f'{now} Загружен токен бота {TOKEN}', flush=True)
bot = TeleBot(TOKEN)

# def COMPANYLOOKUP(input):
#     response=UrlFetchApp.fetch("https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn="+input).getContentText();
#     return response;

def COMPANYLOOKUP(input):
    url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
    response = requests.get(url)
    return response.text

def parse_sudact(data):
    soup = BeautifulSoup(data, 'html.parser')

#запрос данных к sudact.ru
#https://sudact.ru/regular/doc/?regular-txt=Иванов+И.И.&regular-case_doc=&regular-lawchunkinfo=&regular-date_from=&regular-date_to=&regular-workflow_stage=&regular-area=1013&regular-court=&regular-judge=#searchResult
def sudact(request):
    base_url = "https://sudact.ru/regular/doc/"
    params = {
        "regular-txt": request,
        "regular-case_doc": "",
        "regular-lawchunkinfo": "",
        "regular-date_from": "",
        "regular-date_to": "",
        "regular-workflow_stage": "",
        "regular-area": "1013",
        "regular-court": "",
        "regular-judge": ""
    }
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(base_url, params=params, verify=False)  # Отключаем проверку SSL
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса данных по ФИО: {e}", flush=True)
        return None

#отправка в виде нескольких сообщений
def send_big_message(bot, chat_id, message, max_length=4096):
    """Отправляет сообщение в несколько частей, если оно превышает лимит."""
    for i in range(0, len(message), max_length):
        part = message[i:i + max_length]
        bot.send_message(chat_id=chat_id, text=part)

#Основное меню
@bot.message_handler(content_types=["text"])
def next_message(message):
    now = datetime.datetime.now()
    print(f"{now} Получено сообщение: {message.text}", flush=True)  # Логирование входящих сообщений
    #from news.models import TelegramSubscriber
    chat_id = message.chat.id
    username = message.from_user.username
    if message.text.lower() == '/law_order':
        keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1')
        button2 = types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2')
        button3 = types.InlineKeyboardButton('Найти информацию по имени', callback_data='key3')
        keyboard_subcategory.add(button1, button2, button3)

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
            
    elif message.text.startswith("ФИЗ:"):
        keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
        button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
        keyboard_subcategory.add(button_back)

        try:
            full_name = message.text.split(":")[1].strip()
            name_parts = full_name.split()
            fiz_surname = name_parts[0]
            if len(name_parts) > 1:
                initials = f"{name_parts[1][0]}.{name_parts[2][0]}." if len(name_parts) > 2 else f"{name_parts[1][0]}."
                fiz_name = initials
            else:
                fiz_name = ""
            request_fiz = f"{fiz_surname}+{fiz_name}"
            now = datetime.datetime.now()
            print(f"{now} получено имя для запроса: {request_fiz}", flush=True)
            response = sudact(request_fiz)
            print(f"{now} получен ответ от sudact.ru: {response}", flush=True)
            if response:
                # bot.send_message(chat_id, f"Результаты запроса для: {full_name}:\n{response}", reply_markup=keyboard_subcategory)
                #отправка длинного сообщения
                send_big_message(bot, chat_id, response)
            else:
                bot.send_message(chat_id, f"Произошла ошибка при запросе информации по {full_name} к сервису sudact.ru", reply_markup=keyboard_subcategory)
        except Exception as e:
            now = datetime.datetime.now()
            print(f"{now} Ошибка при обработке ФИЗ: {e}", flush=True)
            bot.send_message(chat_id, "Произошла ошибка при обработке запроса. Проверьте формат данных.", reply_markup=keyboard_subcategory)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'key0':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1'),
                types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2'),
                types.InlineKeyboardButton('Найти информацию по имени', callback_data='key3'))
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
    elif call.data == 'key3':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text('Введите имя для запроса в формате: ФИЗ:Иванов Иван Иванович', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
    elif call.data.startswith('ИНН:'):
        inn_id = call.data.split(':')[1]
        now = datetime.datetime.now()
        print(f"{now} Получен ИНН:{inn_id}", flush=True)
        inn_request = COMPANYLOOKUP(inn_id)
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text(f'Получены данные по ИНН:{inn_id} \n{inn_request}', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
#запуск бота через supervisord
def run_bot():
    now = datetime.datetime.now()
    print(f"{now} Запуск Telegram-бота...", flush=True)
    try:
        # Запуск polling с настройкой тайм-аутов
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        now = datetime.datetime.now()
        print(f"{now} Ошибка: {e}", flush=True)
if __name__ == "__main__":
    run_bot()