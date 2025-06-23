from celery import shared_task
# import time
import requests
from bs4 import BeautifulSoup
# для редиски
# import uuid
import redis
from LawOrderParser.utils.redis_client import redis_client
# Подключение к Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
#решение проблем с ajax запросами
from urllib.parse import urlparse, parse_qs

@shared_task(bind=True)
def parse_document(self, redis_key, mode=None):

    print(f"Вызов задачи parse_document с ключом redis {redis_key}")
    url = redis_client.get(redis_key)
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params = {k: v[0] for k, v in params.items()}
        doc_id = parsed.path.strip("/").split("/")[-1]
        ajax_url = "https://sudact.ru/regular/doc_ajax/"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": url,
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }
        params["id"] = doc_id
        response = requests.get(ajax_url, headers=headers, params=params, timeout=10, verify=False)
        if response.status_code != 200:
            return {"ok": False, "message": f"Ошибка загрузки AJAX-контента: {response.status_code}"}

        html_content = response.json().get("content", "")
        soup = BeautifulSoup(html_content, "html.parser")
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

    # try:
        # url = redis_client.get(redis_key)
        # if not url:
        #     print(f"Ключ {redis_key} устарел или не найден.")
        #     return {"ok": False, "message": f"Ключ {redis_key} не найден в Redis."}

        # url = url.decode() if isinstance(url, bytes) else url
        # print(f"Начало парсинга документа по ссылке: {url}")

        # headers = {
        #     "User-Agent": (
        #         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        #         "AppleWebKit/537.36 (KHTML, like Gecko) "
        #         "Chrome/114.0.0.0 Safari/537.36"
        #     )
        # }

        # response = requests.get(url, headers=headers, timeout=10)
        # if response.status_code != 200:
        #     print(f"Не удалось загрузить страницу. Код: {response.status_code}")
        #     return {"ok": False, "message": f"Ошибка загрузки страницы: {response.status_code}"}

        # soup = BeautifulSoup(response.text, "html.parser")
        # headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

        print("Заголовки:", headings)
        return {"ok": True, "headings": headings, "url": url}

    except Exception as e:
        print(f"[EXCEPTION] Ошибка при парсинге документа: {e}")
        return {"ok": False, "message": f"❌ Ошибка при парсинге документа: {str(e)}"}
