# Використовуємо базовий образ Python 3.12 на основі Alpine Linux
FROM python:3.12-alpine

# Вимикаємо буферизацію виводу Python і забороняємо створення *.pyc файлів
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Відкриваємо порт 8000 для додатка
EXPOSE 8000

# Оновлюємо пакети та встановлюємо інструменти для компіляції
RUN apk update && \
    apk add --update --no-cache \
    build-base linux-headers

# Створюємо користувача для запуску додатка
ARG user=fastapi_user
RUN adduser $user --disabled-password

# Створюємо директорію /app і надаємо права користувачу
RUN mkdir -p /app && chown -R $user /app

# Додаємо файл requirements.txt у контейнер
ADD ./requirements.txt ./requirements.txt

# Переходимо на користувача fastapi_user
USER $user

# Додаємо шлях до локальних Python-бінарних файлів у PATH
ENV PATH "$PATH:/home/$user/.local/bin"

# Оновлюємо pip і встановлюємо залежності з requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь код додатка в робочу директорію контейнера
COPY . /app

# Запускаємо FastAPI-додаток через uvicorn
CMD ["uvicorn", "book_api:app", "--host", "0.0.0.0", "--port", "8000"]