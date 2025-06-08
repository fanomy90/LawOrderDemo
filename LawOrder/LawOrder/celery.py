import os
from celery import Celery
from celery.signals import worker_ready
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LawOrder.settings')
app = Celery('LawOrder')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.broker_connection_retry_on_startup = True

# <-- ВАЖНО: Автоматический autodiscover задач -->
app.autodiscover_tasks(['LawOrderParser'])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print('Request: {}'.format(self.request))