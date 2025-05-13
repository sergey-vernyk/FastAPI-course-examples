# Запуск контейнерів docker compose та перевірка їх статусів 

Якщо у вас встановлений `Docker Desktop` на `Windows`, то перед запуском команд нижче необхідно його запустити, щоб engine докера був запущений у вас в системі.

Перед запуском команди треба в терміналі перейти до директорії, де знаходиться ваш `docker-compose.yml` файл.

## Що таке docker-compose.yml?
Це конфігураційний файл, який описує:
- Сервіси (наприклад, frontend, backend, db).
- Мережі, через які ці сервіси взаємодіють.
- Томи для збереження даних.

Та інші конфігурації сервісів.

```bash
# явна вказівка розташування файлу докер композу
docker-compose -f docker-compose.yaml up --build

# якщо файл знаходиться там же де і відкритий термінал, то шлях до файлу можна опустити
docker-compose up --build
```

- `up` - запускає всі сервіси, визначені в docker-compose.yml.
- `--build` - перезбирає образи перед запуском, якщо були зміни в `Dockerfile`.

Під час першого запуску треба вказати параметр `--build`, щоб `images` для сервісів `frontend` та `backend` були створені із поточних `Dockerfile`, які знаходяться в відповідних директоріях.

Подальші запуски можна робити простіше:
```bash
docker-compose -f docker-compose.yaml up
# або
docker-compose up
```

## Зверніть увагу
Команда для роботою із докер композом може бути записана та/або записана як `docker-compose` або `docker compose` без або з дефісом. Це залежить від версії API докера, який встановлений у вас.

Щоб подивитись взагалі, чи докер/докер композ встановлений можна написати команду:

```bash
docker --version 
Docker version 28.1.1, build 4eba377327

docker-compose --version 
Docker Compose version 2.35.1

# або
docker compose version 
Docker Compose version 2.35.1
```

Як видно, в мене на машині встановлена версія **2.35.1** `Docker Compose` та версія **28.1.1** `Docker`. У вас можуть бути інші версії.

### Так виглядає структура наших директорій із файлами.
```bash
.
├── backend
│   ├── book_api.py
│   ├── Dockerfile  # Dockerfile нашого бекенду
│   ├── image.png
│   └── __init__.py
├── docker-compose.yml # Основний файл композу із нашими сервісами для запуску
├── frontend
│   └── frontend-books
│       ├── babel.config.js
│       ├── Dockerfile # Dockerfile нашого фронтенду
│       ├── jsconfig.json
│       ├── package.json
│       ├── package-lock.json
│       ├── public
│       │   ├── favicon.ico
│       │   └── index.html
│       ├── README.md
│       ├── src
│       │   ├── App.vue
│       │   ├── assets
│       │   │   └── logo.png
│       │   ├── components
│       │   │   └── HelloWorld.vue
│       │   └── main.js
│       └── vue.config.js
├── __init__.py
└── Docker Compose Manual.md
```

Щоб подивитись, які сервіси (контейнери) існують в на машині, можна використати наступні команди:

```bash
docker ps -a # усі контейнери, включаючи не запущені
docker ps # тільки запущені контейнери
```

Звичайно, інформацію про контейнери можна подивитись через GUI `Docker Desktop`, проте вміти користуватись командним рядком також необхідно.

Приклади:
```bash
# тільки запущені контейнери
docker ps

CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS                    PORTS                                                    NAMES
89205d17200f   mysql         "docker-entrypoint.s…"   22 seconds ago   Up 21 seconds (healthy)   33060/tcp, 0.0.0.0:3307->3306/tcp, [::]:3307->3306/tcp   mysql-database
d2b20c9694c4   12-frontend   "docker-entrypoint.s…"   21 hours ago     Up 10 seconds             0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp              vue-frontend
0113cb9b765d   12-backend    "uvicorn book_api:ap…"   21 hours ago     Up 10 seconds             0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp              fastapi-backend
```

Як видно, запущені лише наші контейнери з нашого `docker-compose.yml` файлу.

```bash
# всі контейнери
docker ps -a

CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS                     PORTS                                                    NAMES
89205d17200f   mysql                  "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)     33060/tcp, 0.0.0.0:3307->3306/tcp, [::]:3307->3306/tcp   mysql-database
d2b20c9694c4   12-frontend            "docker-entrypoint.s…"   21 hours ago    Up About a minute          0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp              vue-frontend
0113cb9b765d   12-backend             "uvicorn book_api:ap…"   21 hours ago    Up About a minute          0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp              fastapi-backend
8b33e29cfa3d   backend_stage          "sh -c '/bin/wait-fo…"   3 weeks ago     Exited (137) 5 days ago                                                             celery-beat-stage
fb898c837df2   backend_stage          "sh -c '/bin/wait-fo…"   3 weeks ago     Exited (137) 5 days ago                                                             flower-monitoring-stage
5eaa4c98feac   backend_stage          "sh -c '/bin/wait-fo…"   3 weeks ago     Exited (137) 5 days ago                                                             celery-worker-stage
```

Тут вже відображені не тільки запущені наші контейнери, але й не запущені на даний момент контейнери в системі.

## Важливо 
Також не забудьте створити `.env` файл в цій директорії на одному рівні із директоріями `frontend` та `backend` із даними файлу `.env.example`. Можна просто перейменувати цей файл в `.env` і переписати дані для підключення до БД MySQL на якісь свої.

## Зверніть увагу

Значення змінної `MYSQL_HOST` в `.env` файлі повинно точно відповідати назві сервісу з БД MySQL в `docker-compose.yml` файлі. Зараз у нас сервіс БД MySQL в файлі має назву `db`, тому зараз у нас в файлі `.env` є наступне - `MYSQL_HOST="db"`

```yml
# docker-compose.yml

services:
  db: # назва сервісу БД
    image: mysql
    restart: always
    container_name: mysql-database
    ...
# інші рядки
  backend: # назва сервісу нашого бекенду
    build:
      context: ./backend
      dockerfile: ./Dockerfile
    container_name: fastapi-backend
    ...
# інші рядки
  frontend: # назва сервісу нашого фронтенду
    build:
      context: ./frontend/frontend-books
      dockerfile: ./Dockerfile
    container_name: vue-frontend
    ...
# інші рядки
```
Всі сервіси в `docker-compose.yml` працюють в одній спільній мережі і тому кожний запущений сервіс (контейнер) має свою IP адресу. Щоб це побачити, можна написати наступні команди:

```bash
  # приклад IP адрес сервісів (контейнерів) в мене на машині
  # формат команди: docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <назва контейнеру>
  docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-database
  172.24.0.2 # IP серверу MySQL

  docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' fastapi-backend
  172.24.0.3 # IP серверу fastapi бекенду

  docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' vue-frontend
  172.24.0.4 # IP серверу vue фронтеду
```

Команда `inspect` показує детальну інформацію про контейнер, включаючи IP-адресу, змінні середовища і т.д. В прикладі вище був застосований формат (`-f`) де ми дістали тільки необхідну інформацію - IP контейнера.

За рахунок цього кожен контейнер може спілкуватись з один з одним, використовуючи їх IP адреси. Система доменних імен DNS докеру сама конвертує назву сервісу (db, backend, frontend) в IP адресу і надсилає/приймає дані тому адресату, якому потрібно. Так само DNS працює і в глобальній мережі інтернет, де на кожен домен (google.com, youtube.com і т.д.) DNS повертає глобальну IP адресу і спілкування між клієнтом і сервером здійснюється далі за допомогою IP адрес.

Щоб зупинити всі контейнери і мережу, то необхідна команда:

```bash
docker-compose down
```