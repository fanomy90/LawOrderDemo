import requests
from requests.exceptions import RequestException
import urllib3
from bs4 import BeautifulSoup
import datetime
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def parsing_sudact(input):
    # input = "https://sudact.ru/regular/doc/?page=3&regular-txt=Иванов+И.И.&regular-case_doc=&regular-lawchunkinfo=&regular-date_from=&regular-date_to=&regular-workflow_stage=&regular-area=1013&regular-court=&regular-judge=#searchResult"
    now = datetime.datetime.now()
    print(f"{now} начинаем парсить полученные данные из sudact.ru", flush=True)
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 OPR/68.0.3618.125'
        }
        
        #response = requests.get(input, headers=headers, timeout=20, verify=False)
        for _ in range(3):
            try:
                response = requests.get(input, headers=headers, timeout=20, verify=False)
                break
            except RequestException as e:
                print(f"{now} Ошибка при обращении к сайту sudact: {e}", flush=True)
                time.sleep(5)
        else:
            print(f"{now} Запрос данных с сайта sudact не удался после 3 попыток, проверьте доступность сайта")
            return
        if response.status_code == 200:
            print(f"{now} Сайт sudact доступен, начинаем парсить теги")
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            posts_ul = soup.find("ul", class_='results')
            if not posts_ul:
                print(f"{now} Теги ul с классом 'results' не найдены на странице")
                return
            #print(f"Найдено {len(posts)} результатов: {posts}")
            posts_li = posts_ul.find_all("li")
            print(f"{now} Найдено {len(posts_li)} элементов li в ul.results")


            results= []
            for post_li in posts_li:
                # Извлекаем название и ссылку на каждый документ
                link_tag = post_li.find("a")
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    url = "https://sudact.ru" + link_tag['href']
                    results.append({'title': title, 'url': url})
            for result in results:
                print(f"Название: {result['title']}, Ссылка: {result['url']}")
        else:
            print(f"{now} Код ответа от сайта sudact: {response.status_code}")
            # posts_links = []
            # posts_data = []
            # for post in posts:
            #     href = a_tag['href']
            #     title = 
    except Exception as e:
        print(f"{now} Парсинг данных с сайта sudact.ru завершился с ошибкой: {e}")
        return

#вызов парсинга для теста
if __name__ == "__main__":
    parsing_sudact("https://sudact.ru/regular/doc/?page=1&regular-txt=Иванов+М.А.&regular-case_doc=&regular-lawchunkinfo=&regular-date_from=&regular-date_to=&regular-workflow_stage=&regular-area=1013&regular-court=&regular-judge=#searchResult")
    # parsing_sudact("https://sudact.ru/regular/doc/?page=1&regular-txt=Иванов+И.И.&regular-case_doc=&regular-lawchunkinfo=&regular-date_from=&regular-date_to=&regular-workflow_stage=&regular-area=1013&regular-court=&regular-judge=#searchResult")
    #parsing_sudact("https://sudact.ru/regular/doc/?regular-txt=Иванов+И.И.&regular-case_doc=&regular-lawchunkinfo=&regular-date_from=&regular-date_to=&regular-workflow_stage=&regular-area=1013&regular-court=&regular-judge=#searchResult")