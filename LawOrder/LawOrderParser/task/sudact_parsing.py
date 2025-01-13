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
                # number = post_li.find(class_="numb")
                # заголовок и ссылка на документа
                #краткое описание в документе
                #post = post_li.get_text(strip=True)
                #clean_post = clean_text(post)
                # print(f"{now} Очищенный текст clean_post: {clean_post}")
                # post = post_li.get_text(separator=' ', strip=True)
                # post_parts = post.split('...')
                # if len(post_parts) > 1:
                #     # Извлекаем второй фрагмент после первого '...'
                #     extracted_text = post_parts[1].strip()  # Удаляем лишние пробелы
                #     clean_post = clean_text(extracted_text)
                #     print("Извлеченный текст:", clean_post)
                # else:
                #     print("Не удалось найти текст после '...'")
                link_tag = post_li.find("a")
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    url = "https://sudact.ru" + link_tag['href']
                    
                    # results.append({'title': title, 'url': url})
                    results.append({
                        'number': number, 
                        'title': title, 
                        'url': url, 
                        # 'clean_dispute': clean_dispute,
                        # 'snippet': snippet,
                        # 'clean_post': clean_post
                        })
            #for result in results:
                #print(f"Название: {result['title']}, Ссылка: {result['url']}")
            return results, total_results
        else:
            print(f"{now} Код ответа от сайта sudact: {response.status_code}")
            return None, 0
    except Exception as e:
        print(f"{now} Парсинг данных с сайта sudact.ru завершился с ошибкой: {e}")
        return None, 0