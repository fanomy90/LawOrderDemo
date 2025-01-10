FROM python:3.11.2

SHELL ["/bin/bash", "-c"]
# Настройки виртуального окружения: запрет создания кэш файлов и запрет буферизации сообщений с логами 
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Обновим pip
# RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y curl && apt-get clean
WORKDIR /yt
COPY ./requirements.txt /yt/
# Установим зависимости проекта
RUN pip install -r requirements.txt
# Установка supervisord
RUN apt-get install -y supervisor
# Копируем конфигурацию supervisord
COPY ./supervisord.conf /etc/supervisor/supervisord.conf
COPY .env .env
COPY ./LawOrder /yt/
RUN chmod +x /yt/LawOrderBot/TeleBot.py

CMD python manage.py migrate \ 
    # создание суперпользователя
    && python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='root').exists() or User.objects.create_superuser('root', 'root@example.com', 'root')" \
    # && python manage.py initialize_db \
    && python manage.py collectstatic --noinput \
    # && python manage.py runserver 0.0.0.0:9000
    # && gunicorn --bind 0.0.0.0:9000 --workers 3 --access-logfile - --error-logfile - puppeteer.wsgi:application
    && python manage.py makemigrations \
    && python manage.py migrate \
    # && python news/slow_bot.py & \
    # && daphne -b 0.0.0.0 -p 9000 puppeteer.asgi:application
    && supervisord -c /etc/supervisor/supervisord.conf