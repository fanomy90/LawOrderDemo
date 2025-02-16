import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import requests
import urllib3
from bs4 import BeautifulSoup
import datetime
from urllib.parse import urlencode
import time
from requests.exceptions import RequestException
from celery import shared_task
from django.conf import settings

# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Добавляем корневую директорию в PYTHONPATH
sys.path.append(project_root)
# Укажите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawOrder.settings')
import django
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
        if not response:
            print(f"{now} Запрос данных с сайта sudact не удался после 3 попыток")
            return None, 0
        else:
            print(f"{now} Запрос данных с сайта sudact не удался после 3 попыток, проверьте доступность сайта")
        if response.status_code != 200:
            print(f"{now} Код ответа от сайта sudact: {response.status_code}")
            return None, 0
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
            if not search_result:
                print(f"{now} Тег div.prompting не найден, предполагаем, что total_results = 0")
            #нужно использовать total_results для парсинга найденныз результатов и перехода к следующим параметрам поиска - использовать конструктор поиска
            print(total_results)
            #ищем ссылки на решения судов - нужно парсить данные ссылки и записывать данные в БД
            posts_ul = soup.find("ul", class_='results')
            if not posts_ul:
                print(f"{now} Теги ul с классом 'results' не найдены на странице")
                return
            posts_li = posts_ul.find_all("li")
            if not posts_li:
                print(f"{now} Данные для парсинга не найдены.")
                return [], total_results
            print(f"{now} Найдено {len(posts_li)} элементов li в ul.results")
            results= []
            for post_li in posts_li:
                # номер документа
                numb = post_li.find("span", class_="numb")
                # if not numb:
                #     print(f"{now} Элемент span.numb не найден в li")
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

# блок для формирования страницы поиска на сайте
@shared_task(bind=True, time_limit=60, soft_time_limit=30)
# def sudact_find():
def sudact_find(self, mode=None):
    try:
        # раздел
        category = "Суды общей юрисдикции"
        # параметры поиска: дата с по
        date_from = "02.01.2024"
        date_to = "02.01.2024"
        # area
        # region = "Ленинградская область"
        region = "1014"
        # инстанция
        # instance = "Первая инстанция"
        instance = "10"

        # нормализация поисковыъ параметров для формирования запроса к сайту
        request_url = finds_url(category, date_from, date_to, instance, region)
        if not request_url:
            print(f"{now} Ошибка формирования URL для поиска")
            return
        # запуск парсера с выбранными парпаметрами 
        
        response_regular, regular_total = parse_sudact(request_url)

        if response_regular is not None:
            print(f"{now} Успешно обработано: {len(response_regular)} результатов, всего найдено: {regular_total}")
        else:
            print(f"{now} Парсинг завершился неудачно")
    except Exception as e:
        now = datetime.datetime.now()
        print (f"{now} найдено {regular_total} результатов")