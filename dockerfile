# Используем базовый образ Python
FROM python:3.9
SHELL ["/bin/bash", "-c"]
# Настройки виртуального окружения: запрет создания кэш файлов и запрет буферизации сообщений с логами 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl && apt-get clean
# Устанавливаем рабочую директорию
WORKDIR /app
# Копируем файл зависимостей (если есть) и устанавливаем зависимости
COPY requirements.txt requirements.txt
# Копируем файл зависимостей (если есть) и устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
# Копируем остальные файлы приложения
#COPY . .
COPY .env .env
COPY LawOrderBot.py LawOrderBot.py
RUN chmod +x LawOrderBot.py
# Команда для запуска скрипта
CMD ["python", "LawOrderBot.py"]