import os
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import datetime
from urllib.parse import urlencode
import time
from requests.exceptions import RequestException
from celery import shared_task
from django.conf import settings
from urllib.parse import urlparse, parse_qs
# отключить предупреждения от urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from LawOrderParser.utils.redis_client import redis_client
# Проверить
from dotenv import load_dotenv
import django
# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Добавляем корневую директорию в PYTHONPATH
sys.path.append(project_root)
# Укажите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawOrder.settings')
django.setup()
#нормализация полей для формирования поиска на сайте
def finds_url(category, date_from, date_to, instance, region, page=1):
    
    if category == "Суды общей юрисдикции":
        base_url = "https://sudact.ru/regular/doc/"
        params = {
            "page": page,
            # "regular-txt": request,
            "regular-txt": "",
            "regular-case_doc": "",
            "regular-lawchunkinfo": "",
            "regular-date_from": date_from,
            "regular-date_to": date_to,
            "regular-workflow_stage": instance,
            # "regular-area": "1013",
            "regular-area": region,
            "regular-court": "",
            "regular-judge": ""
        }
    elif  category == "Мировые суды":
        base_url = "https://sudact.ru/magistrate/doc/"
        params = {
            "page": page,
            # "magistrate-txt": request,
            "magistrate-txt": "",
            "magistrate-case_doc": "",
            "magistrate-lawchunkinfo": "",
            "magistrate-date_from": date_from,
            "magistrate-date_to": date_to,
            #"magistrate-workflow_stage": "",
            "magistrate-area": region,
            "magistrate-court": "",
            "magistrate-judge": ""
        }
    else:
        raise ValueError(f"Неизвестная категория: {category}")
    try:
        query_string = urlencode(params)
        request_url = f"{base_url}?{query_string}"
        now = datetime.datetime.now()
        print(f"{now} Сформирована ссылка для поиска: {request_url}", flush=True)
        return request_url
    except requests.exceptions.RequestException as e:
        print(f"Ошибка формирование ссылки для поиска: {e}", flush=True)
        return None

def parse_sudact(input_url):
    now = datetime.datetime.now()
    print(f"{now} Начинаем парсить данные из sudact.ru", flush=True)
    try:
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        #     "X-Requested-With": "XMLHttpRequest"
        # }
        headers = {
            "User-Agent": "...",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": input_url,  # тот, который был сгенерирован ранее
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        # Извлекаем параметры из URL
        parsed = urlparse(input_url)
        query_params = parse_qs(parsed.query)
        # Преобразуем значения из списка в строку
        params = {k: v[0] for k, v in query_params.items()}
        ajax_url = "https://sudact.ru/regular/doc_ajax/"

        response = None
        for _ in range(3):
            try:
                # response = requests.get(ajax_url, headers=headers, params=params, timeout=20)
                # вариант с отключенной проверкой ssl
                response = requests.get(ajax_url, headers=headers, params=params, timeout=20, verify=False)
                break
            except RequestException as e:
                print(f"{now} Ошибка при обращении к sudact: {e}", flush=True)
                time.sleep(5)
        if response is None or response.status_code != 200:
            print(f"{now} Не удалось получить данные: код {response.status_code if response else 'нет ответа'}")
            return None, 0
        # парсим JSON и вытаскиваем HTML
        json_data = response.json()
        html_content = json_data.get("content", "")
        # отладка полученного ответа
        # print(f"{now} Первые 2000 символов HTML-ответа:\n{src[:2000]}")
        print(f"HTML ответ:\n{response.text[:1000]}")
        # soup = BeautifulSoup(response.text, 'lxml')
        soup = BeautifulSoup(html_content, 'lxml')
        posts_li = soup.select("ul.results > li")
        if not posts_li:
            print(f"{now} Данные не найдены.")
            return [], 0
        print(f"{now} Найдено {len(posts_li)} записей")
        results = []
        for post_li in posts_li:
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
        # Пробуем вытащить количество результатов
        search_result = soup.find("div", class_='prompting')
        # total_results = 0
        # if search_result:
        #     total_text = search_result.get_text(strip=True)
        #     total_results = int(''.join(filter(str.isdigit, total_text))) if any(c.isdigit() for c in total_text) else 0
        total_results = len(posts_li)
        return results, total_results
    except Exception as e:
        print(f"{now} Ошибка парсинга sudact.ru: {e}")
        return None, 0

def sudact_find(mode=None):
    now = datetime.datetime.now()
    result_message = f"{now} Запуск парсинга, режим: {mode}\n"
    #данные в виде словаря для возможности из обработки и загрузки в БД
    parsed_items = []
    try:
        category = "Суды общей юрисдикции"
        date_from = "02.01.2024"
        date_to = "02.01.2024"
        region = "1014"
        instance = "10"
        request_url = finds_url(category, date_from, date_to, instance, region)
        if not request_url:
            result_message += "Ошибка формирования URL для поиска"
            print(result_message)
            return result_message, []
        response_regular, regular_total = parse_sudact(request_url)
        if response_regular:
            msg = f"Успешно обработано: {len(response_regular)} результатов, всего найдено: {regular_total}"
            result_message += msg + "\n"
            print(msg)
            for item in response_regular:
                parsed_items.append(item)
                # часть ниже необязательна так как можно обработать на стороне бота эти данные из parsed_items
                result_message += f"№{item['number']} {item['title']}\nСсылка: {item['url']}\n\n"
        else:
            msg = "Парсинг завершился неудачно"
            result_message += msg
            print(msg)
            return result_message, []
    except Exception as e:
        result_message += f"❌ Ошибка: {str(e)}"
        print(result_message)
        return result_message, []
    return result_message, parsed_items