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

#нормализация полей для формирования поиска на сайте
def find_normalize(category, date_from, date_to, instance, page):
    
    if category == "Суды общей юрисдикции"
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

            "regular-area": "",

            "regular-court": "",
            "regular-judge": ""
        }

    if category == "Мировые суды"
        base_url = "https://sudact.ru/magistrate/doc/"
        params = {
            "page": page,
            # "magistrate-txt": request,
            "magistrate-txt": "",
            "magistrate-case_doc": "",
            "magistrate-lawchunkinfo": "",
            "magistrate-date_from": "",
            "magistrate-date_to": "",
            #"magistrate-workflow_stage": "",

            "magistrate-area": "",

            "magistrate-court": "",
            "magistrate-judge": ""
        }



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
            #нужно использовать total_results для парсинга найденныз результатов и перехода к следующим параметрам поиска - использовать конструктор поиска
            print(total_results)
            #ищем ссылки на решения судов - нужно парсить данные ссылки и записывать данные в БД
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

# блок для формирования страницы поиска на сайте
def sudact_find():
    try:
        # раздел
        category = "Суды общей юрисдикции"
        # параметры поиска: дата с по
        date_from = "02.01.2024"
        date_to = "02.01.2024"
        # area
        region = "Ленинградская область"
        # инстанция
        instance = "Первая инстанция"
        # нормализация поисковыъ параметров для формирования запроса к сайту
        find_normalize(category, date_from, date_to, instance)
        # запуск парсера с выбранными парпаметрами 
        parse_sudact() 