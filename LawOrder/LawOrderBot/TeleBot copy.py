import sys
sys.path.append('/yt')
import telebot
from telebot import types, TeleBot
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import urllib3
from bs4 import BeautifulSoup
import datetime
from urllib.parse import urlencode
import time
from requests.exceptions import RequestException
import csv
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from LawOrderParser.tasks import parsing

# from LawOrderParser.models import *
from LawOrderParser import models

# Загрузка переменных окружения из файла .env
# load_dotenv()
# TOKEN = os.getenv("TOKEN")
# if not TOKEN or ":" not in TOKEN:
#     raise ValueError(f"Ошибка: Загруженный токен `{TOKEN}` невалиден")
# now = datetime.datetime.now()
# print(f'{now} Загружен токен бота {TOKEN}', flush=True)
# # bot = TeleBot(TOKEN)
# # bot = TeleBot(str(TOKEN).strip())
# bot = telebot.TeleBot("7300227909:AAG-e8fsDro4SXWueGXN-CV6KGuShcorchU")

now = datetime.datetime.now()
TOKEN = "7300227909:AAG-e8fsDro4SXWueGXN-CV6KGuShcorchU"

print(f"{now} Загружен токен бота: `{TOKEN}` (длина: {len(TOKEN)})", flush=True)

# Дополнительные проверки
if not isinstance(TOKEN, str):
    raise TypeError(f"ОШИБКА: Токен должен быть строкой, но сейчас это {type(TOKEN)}")

if ":" not in TOKEN:
    raise ValueError(f"ОШИБКА: Токен `{TOKEN}` не содержит двоеточие!")

bot = telebot.TeleBot(TOKEN)
print("✅ Бот успешно создан!")

#Вспомогательные функции
def COMPANYLOOKUP(input):
    url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
    response = requests.get(url)
    return response.text

# Преобразует DecimalField в строку без .0
def safe_decimal(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(int(value))
    return str(value)

def load_area():
    area = {}
    try:
        # чтение регионов из БД
        for region in models.Region.objects.all():
            area[region.region_name] = {
                'arbitral_area': str(region.arbitral_region) if region.arbitral_region else "",
                'regular_area': str(region.regular_region) if region.regular_region else "",
                'magistrate_area': str(region.magistrate_region) if region.magistrate_region else "",
            }
        now = datetime.datetime.now()
        print(f'{now} Загружен список городов: {area}', flush=True)
    except Exception as e:
        print(f"Ошибка при загрузке регионов: {e}", flush=True)
    return area
#формирование клавиатуры выбора города
# def area_keyboard(areas):
def area_keyboard(areas):
    # areas = load_area()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for area, data in areas.items():
        callback_data = f"area:{area},{data['regular_area']},{data['magistrate_area']}"
        keyboard.add(InlineKeyboardButton(area, callback_data=callback_data))
    keyboard.add(InlineKeyboardButton("Назад", callback_data="key0"))
    return keyboard
#очистка текста перед отправкой ботом
def clean_text(text):
    import html
    import re
    text = html.escape(text)  # Экранирует HTML-спецсимволы
    text = re.sub(r'<[^>]+>', '', text)  # Удаляет HTML-теги
    return text
#парсинг страницы поиска результатов
def parse_sudact(input):
    now = datetime.datetime.now()
    print(f"{now} начинаем парсить полученные данные из sudact.ru", flush=True)
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 OPR/68.0.3618.125'
        }
        for _ in range(3):
            try:
                response = requests.get(input, headers=headers, timeout=20, verify=False)
                break
            except RequestException as e:
                print(f"{now} Ошибка при обращении к сайту sudact: {e}", flush=True)
                time.sleep(5)
        else:
            print(f"{now} Запрос данных с сайта sudact не удался после 3 попыток, проверьте доступность сайта")
        if response.status_code == 200:
            print(f"{now} Сайт sudact доступен, начинаем парсить теги")
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            #ищем общее количество найденных результатов
            search_result = soup.find("div", class_='prompting')
            total_results = 0  # По умолчанию, если div.prompting не найден
            if search_result:
                total_text = search_result.get_text(strip=True)
                print(f"{now} Текст из 'prompting': {total_text}")
                total_results = int(''.join(filter(str.isdigit, total_text))) if any(char.isdigit() for char in total_text) else 0
            print(total_results)
            #ищем ссылки на решения судов
            posts_ul = soup.find("ul", class_='results')
            if not posts_ul:
                print(f"{now} Теги ul с классом 'results' не найдены на странице")
                return
            posts_li = posts_ul.find_all("li")
            print(f"{now} Найдено {len(posts_li)} элементов li в ul.results")
            results= []
            for post_li in posts_li:
                # номер документа
                numb = post_li.find("span", class_="numb")
                number = numb.get_text(strip=True) if numb else ''
                link_tag = post_li.find("a")
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    url = "https://sudact.ru" + link_tag['href']
                    results.append({
                        'number': number, 
                        'title': title, 
                        'url': url, 
                        })
            return results, total_results
        else:
            print(f"{now} Код ответа от сайта sudact: {response.status_code}")
            return None, 0
    except Exception as e:
        print(f"{now} Парсинг данных с сайта sudact.ru завершился с ошибкой: {e}")
        return None, 0

#Подготовка результатов поиска перед отравкой пользователю
def prepare_message(input):
    message = []
    for i in input:
        number = i['number']
        title = i['title']
        url = i['url']
        content = (
            f'<a href="{url}">{number} {title}</a>\n\n'
        )
        message.append(content)
    # соединим все сообщения в одно с разделителями
    message_text = ''.join(message)
    return message_text
#формирование ссылки для запроса данных в СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ
def sudact(request, page=1):
    base_url = "https://sudact.ru/regular/doc/"
    params = {
        "page": page,
        "regular-txt": request,
        "regular-case_doc": "",
        "regular-lawchunkinfo": "",
        "regular-date_from": "",
        "regular-date_to": "",
        "regular-workflow_stage": "",
        # "regular-area": "1013",
        "regular-area": "",
        "regular-court": "",
        "regular-judge": ""
    }
    try:
        query_string = urlencode(params)
        request_url = f"{base_url}?{query_string}"
        now = datetime.datetime.now()
        print(f"{now} Сформирована ссылка СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ по ФИО: {request_url}", flush=True)

        return request_url
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса данных в СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ по ФИО: {e}", flush=True)
        return None
        
#формирование ссылки для запроса данных в МИРОВЫЕ СУДЫ
def sudact_magistrate(request, page=1):
    base_url = "https://sudact.ru/magistrate/doc/"
    params = {
        "page": page,
        "magistrate-txt": request,
        "magistrate-case_doc": "",
        "magistrate-lawchunkinfo": "",
        "magistrate-date_from": "",
        "magistrate-date_to": "",
        #"magistrate-workflow_stage": "",
        "magistrate-area": "",
        "magistrate-court": "",
        "magistrate-judge": ""
    }
    try:
        query_string = urlencode(params)
        request_url = f"{base_url}?{query_string}"
        now = datetime.datetime.now()
        print(f"{now} Сформирована ссылка МИРОВЫЕ СУДЫ по ФИО: {request_url}", flush=True)
        return request_url
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса данных в МИРОВЫЕ СУДЫ по ФИО: {e}", flush=True)
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
        #button1 = types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1')
        #button2 = types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2')
        button3 = types.InlineKeyboardButton('Найти информацию по имени', callback_data='key3')
        # keyboard_subcategory.add(button1, button2, button3)
        button_regular = types.InlineKeyboardButton('Поиск в судах общей юрисдикции', callback_data='regular')

        button_magistrate = types.InlineKeyboardButton('Поиск в мировых судах', callback_data='magistrate')
        
        button_parse = types.InlineKeyboardButton('Запуск парсера', callback_data='parse')
        
        keyboard_subcategory.add(button3, button_regular, button_magistrate, button_parse)

        bot.send_message(chat_id, 
                    text=f"Добро пожаловать, {username}!\nВыберите действие:",
                    reply_markup=keyboard_subcategory)
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
    # проверка для сообщений, начинающихся сразу с цифр без "ИНН:"
    elif message.text.isdigit() and len(message.text) in [10, 12]:
            inn_id = message.text
            inn_request = COMPANYLOOKUP(inn_id)
            #bot.send_message(chat_id, f"Получены данные по ИНН {inn_id}:\n{inn_request}")
            keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
            button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
            keyboard_subcategory.add(button_back)
            bot.send_message(chat_id, f"Получены данные по ИНН {inn_id}:\n{inn_request}", reply_markup=keyboard_subcategory)
    
    #измененная обработка ввода ФИЗ с выбором раздела сайта sudact
    elif message.text.startswith("ФИЗ:"):
        keyboard_subcategory = None
        page = 1
        parts = message.text.split(',')
        try:
            if len(parts) > 1 and '=' in parts[1]:
                page = int(parts[1].split('=')[1])
            print(f"{now} получена страница для запроса: {page}", flush=True)
            full_name = parts[0].split(":")[1].strip()
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
            
            keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
            button_regular = types.InlineKeyboardButton(
                'Поиск в судах общей юрисдикции', 
                callback_data=f'ФИЗ:{request_fiz},page=1,sudact:regular'
                )
            button_magistrate = types.InlineKeyboardButton(
                'Поиск в мировых судах', 
                callback_data=f'ФИЗ:{request_fiz},page=1,sudact:magistrate')
            button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
            keyboard_subcategory.add(button_regular, button_magistrate, button_back)

            bot.send_message(
                chat_id, 
                f"По запросу ФИЗ: {request_fiz} выберите раздел для поиска \n",
                parse_mode="HTML", 
                reply_markup=keyboard_subcategory
            )
        except Exception as e:
            now = datetime.datetime.now()
            print(f"{now} Ошибка: {e}", flush=True)
            bot.send_message(chat_id, "Произошла ошибка. Проверьте формат запроса.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    areas = load_area()
    if call.data == 'key0':
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        # keyboard_category.add(types.InlineKeyboardButton('Найти информацию по ИНН', callback_data='key1'),
        #         types.InlineKeyboardButton('Архив запросов по ИНН', callback_data='key2'),
        #         types.InlineKeyboardButton('Найти информацию по имени', callback_data='key3'))
        keyboard_category.add(types.InlineKeyboardButton('Найти информацию по имени', callback_data='key3'))

        bot.edit_message_text('Выберите действие:', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
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
    #новый функционал
    elif call.data == 'regular':
        area_path = 'area.csv'
        if not os.path.exists(area_path):
            raise FileNotFoundError(f"Файд {file_path} не найден")

        keyboard = area_keyboard(areas)
        bot.send_message(call.message.chat.id, "Выберите город", reply_markup=keyboard)

    elif call.data == 'parse':
        keyboard = area_keyboard(areas)
        bot.send_message(call.message.chat.id, "Запущен парсер смотри лог выполнения", reply_markup=keyboard)
        # Запуск Celery задачи
        result = parsing.delay()

        # Выводим ID задачи для отладки (по желанию)
        bot.send_message(call.message.chat.id, f"ID запущенной задачи: {result.id}")

    elif call.data.startswith('area:'):
        areas_data = call.data.split(':')[1]
        city, regular_area, magistrate_area = areas_data.split(',')  # Разделяем по запятой
        bot.send_message(call.message.chat.id, f"Выбран город {city} для regular запроса: {regular_area}")
    
    
    elif call.data.startswith('ИНН:'):
        inn_id = call.data.split(':')[1]
        now = datetime.datetime.now()
        print(f"{now} Получен ИНН:{inn_id}", flush=True)
        inn_request = COMPANYLOOKUP(inn_id)
        keyboard_category = types.InlineKeyboardMarkup(row_width=1)
        keyboard_category.add(types.InlineKeyboardButton('Назад', callback_data='key0'),
                )
        bot.edit_message_text(f'Получены данные по ИНН:{inn_id} \n{inn_request}', call.message.chat.id, call.message.message_id, reply_markup=keyboard_category)
    #основной маршрут обработки и вывода результатов поизка документов по физлицу
    elif call.data.startswith('ФИЗ:'):
        try:
            parts = call.data.split(',')
            full_name = parts[0].split(':')[1].strip()
            page = int(parts[1].split('=')[1]) if len(parts) > 1 and '=' in parts[1] else 1
            # Здесь логика обработки смены страницы
            response_regular, regular_total = parse_sudact(sudact(full_name, page))
            regular_results = prepare_message(response_regular)
            
            keyboard_subcategory = types.InlineKeyboardMarkup(row_width=1)
            button_back = types.InlineKeyboardButton('Назад', callback_data='key0')
            if page > 1:
                button_previous = types.InlineKeyboardButton('<', callback_data=f'ФИЗ:{full_name}, page={page-1}')
                keyboard_subcategory.add(button_previous)
            button_next = types.InlineKeyboardButton('>', callback_data=f'ФИЗ:{full_name}, page={page+1}')
            keyboard_subcategory.add(button_next)
            bot.edit_message_text(
                f"По запросу {full_name} найдено {regular_total} документов в разделе \n"
                f"Страница: {page}\n\n"
                f"СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ:\n\n {regular_results}", 
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=keyboard_subcategory
            )
        except Exception as e:
            print(f"call.data.startswith('ФИЗ:'): {e}")

def run_bot():
    now = datetime.datetime.now()
    print(f"{now} Запуск Telegram-бота...", flush=True)
    try:
        # Инициализация бота (например, токен)
        bot = telebot.TeleBot('YOUR_BOT_TOKEN')
        print(f"{now} Токен загружен", flush=True)
        
        # Запуск polling с настройкой тайм-аутов
        print("🚀 Попытка запуска бота...", flush=True)
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        now = datetime.datetime.now()
        print(f"{now} Ошибка: {e}", flush=True)
        time.sleep(10)  # Подождать перед попыткой перезапуска
        run_bot()  # Попробовать перезапустить бота через некоторое время

if __name__ == "__main__":
    run_bot()