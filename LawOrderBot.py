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


# Загрузка переменных окружения из файла .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
now = datetime.datetime.now()
print(f'{now} Загружен токен бота {TOKEN}', flush=True)
bot = TeleBot(TOKEN)

#Вспомогательные функции

# def COMPANYLOOKUP(input):
#     response=UrlFetchApp.fetch("https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn="+input).getContentText();
#     return response;


def COMPANYLOOKUP(input):
    url = f"https://api.datanewton.ru/v1/counterparty?key=lMqXGnVMQAyn&filters=OWNER_BLOCK%2CADDRESS_BLOCK&inn={input}"
    response = requests.get(url)
    return response.text

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
                link_tag = post_li.find("a")
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    url = "https://sudact.ru" + link_tag['href']
                    results.append({'title': title, 'url': url})
            #for result in results:
                #print(f"Название: {result['title']}, Ссылка: {result['url']}")
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
        title = i['title']
        url = i['url']
        content = (
            #f"<b>{title}</b>\n"
            f'<a href="{url}">{title}</a>\n\n'
        )
        message.append(content)
    # соединим все сообщения в одно с разделителями
    message_text = ''.join(message)
    return message_text



#формирование ссылки для запроса данных
def sudact(request):
    base_url = "https://sudact.ru/regular/doc/"
    params = {
        "page": 1,
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
        
        #urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #response = requests.get(base_url, params=params, verify=False)  # Отключаем проверку SSL
        #response.raise_for_status()
        #return response.text
        query_string = urlencode(params)
        request_url = f"{base_url}?{query_string}"
        return request_url
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса данных в СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ по ФИО: {e}", flush=True)
        return None
# https://sudact.ru/regular/doc/
# ?regular-txt=%D0%98%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2%20%D0%9C.%D0%90.&
# regular-case_doc=&
# regular-lawchunkinfo=&
# regular-date_from=&
# regular-date_to=&
# regular-workflow_stage=&
# regular-area=&&
# regular-court=&
# regular-judge=#searchResult
# https://sudact.ru/magistrate/doc/
# ?magistrate-txt=%D0%98%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2%20%D0%9C.%D0%90.&
# magistrate-case_doc=&
# magistrate-lawchunkinfo=&
# magistrate-date_from=&
# magistrate-date_to=&
# magistrate-area=&&
# magistrate-court=&
# magistrate-judge=#searchResult

def sudact_magistrate(request):
    base_url = "https://sudact.ru/magistrate/doc/"
    params = {
        "page": 1,
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
        keyboard_subcategory.add(button3)

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
            #response = sudact(request_fiz)
            #СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ
            response_regular, regular_total = parse_sudact(sudact(request_fiz))
            regular_results = prepare_message(response_regular)
            #print(sudact_result)

            #МИРОВЫЕ СУДЫ
            response_magistrate, magistrate_total = parse_sudact(sudact_magistrate(request_fiz))
            magistrate_results = prepare_message(response_magistrate)

            bot.send_message(
                chat_id, 
                f"По запросу {request_fiz} найдено {regular_total} документов в разделе \n"
                # f"{regular_total}\n\n" 
                f"СУДЫ ОБЩЕЙ ЮРИСДИКЦИИ:\n\n {regular_results}", 
                parse_mode="HTML", 
                reply_markup=keyboard_subcategory
            )
            #bot.send_message(chat_id, message_regular, parse_mode="HTML")
            time.sleep(2)
            #отправка результатов по мировым судам
            #bot.send_message(chat_id, f"По запросу {request_fiz} найдены документы \n\n МИРОВЫЕ СУДЫ:\n\n {response_magistrate}", reply_markup=keyboard_subcategory)
            bot.send_message(
                chat_id, 
                f"По запросу {request_fiz} найдено {magistrate_total} документов в разделе \n"
                # f"{magistrate_total}\n\n" 
                f"МИРОВЫЕ СУДЫ:\n\n {magistrate_results}", 
                parse_mode="HTML", 
                reply_markup=keyboard_subcategory
            )
        except Exception as e:
            now = datetime.datetime.now()
            print(f"{now} Ошибка при обработке ФИЗ: {e}", flush=True)
            bot.send_message(chat_id, "Произошла ошибка при обработке запроса. Проверьте формат данных.", reply_markup=keyboard_subcategory)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
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