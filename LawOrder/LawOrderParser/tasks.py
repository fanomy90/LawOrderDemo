# import sys
# sys.path.append('/yt')
import os
from django.conf import settings
import time
from celery import shared_task
from LawOrderParser.task.sudact_parsing import sudact_find
from celery.utils.log import get_task_logger
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'puppeteer.settings')
import django
django.setup()
logger = get_task_logger(__name__)

@shared_task
def parsing():
    logger.info("Начало выполнения задачи parsing")
    try:
        sudact_find()
        logger.info("Задача parsing выполнена успешно")
    except Exception as e:
        logger.error(f"Ошибка выполнения задачи parsing: {e}")
        raise