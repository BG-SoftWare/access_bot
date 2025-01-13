[ENG](#ENG) || [RUS](#RUS)

# ENG

<h1 align=center>Launch permision controller app</h1>

This project allows you to manage the permission to run applications via telegram bot. 

<h2 align=center>Contents</h2>

1. [Features](#Features)
2. [Technologies](#Technologies)
3. [Preparing to work](#Preparing-to-work-and-usage)
4. [DISCLAIMER](#DISCLAIMER)

## Features
The main features of this bot include:
  + Control launch allowance
  + Search by application id
  + Logging the time of the last check of the application startup permission
  + Authorization via login-password pair
  + Automatically add an application after sending a request from it

## Technologies

| Technology | Description                                            |
|------------|--------------------------------------------------------|
| aiogram    | The library for web and native user interfaces         |
| Redis      | in-memory key-value database, cache and message broker |
| FastAPI    | High-performance web framework for building API        |
| SQLAlchemy | Python SQL toolkit and ORM                             |

## Preparing to work and usage

### Running on system

1. Install [Python 3.10+](https://python.org/)
2. Install [Redis](https://redis.io/)
3. Download the source code of the project
4. Create a virtual environment:
   - On Linux:
     ```bash
     python3 -m venv .venv
     ```
   - On Windows:
     ```bash
     python -m venv .venv
     ```
5. Activate the virtual environment:
   - On Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - On Windows (cmd):
     ```cmd
     .venv\Scripts\activate.bat
     ```
6. Install project dependencies:
   ```bash
   pip install -r telegram_bot/requirements.txt
   ```
7. Copy `env.example` to `telegram_bot/.env` and edit the `.env`.
8. Change directory to `telegram_bot` and run the management utility:
   - On Linux:
     ```bash
     python3 manage.py
     ```
   - On Windows:
     ```cmd
     python manage.py
     ```
   This will launch a utility where you can create a user.
9. Run the bot from the `telegram_bot` directory:
   - On Linux:
     ```bash
     python3 bot.py
     ```
   - On Windows:
     ```cmd
     python bot.py
     ```

### Running with Docker

1. Install [Docker](https://docker.com)
2. Copy `env.example` to `.env` and edit the `.env`.
3. Create a Redis container by running:
   ```bash
   make storage
   ```
4. Run the management utility in a container by executing:
   ```bash
   make manage
   ```
   This will launch a utility where you can add a user.
5. Start the bot in a container by running:
   ```bash
   make up
   ```

In both setups, bot started listening LISTEN_HOST:LISTEN_PORT from `.env`

In order for your application to check the right to run you need to send an HTTP request of the following form:
```
Request type: GET
Path: /
Headers:
"APP_ID_HEADER": ‘com.example.app’.
```

If the response is the string specified in `OK_RESPONSE`, your application can continue to run. If the string `BLOCKED_RESPONSE` is received, your application should terminate.

`OK_RESPONSE`, `BLOCKED_RESPONSE`, `APP_ID_HEADER` are configured in .env

For production use, the bot must be behind nginx




## DISCLAIMER
The user of this software acknowledges that it is provided "as is" without any express or implied warranties. 
The software developer is not liable for any direct or indirect financial losses resulting from the use of this software. 
The user is solely responsible for his/her actions and decisions related to the use of the software.

---

# RUS

<h1 align=center>Контроллер запуска приложений</h1>

Этот проект позволяет управлять правами на запуск приложений через telegram-бота.

<h2 align=center>Содержание</h2>

1. [Особенности](#Особенности)
2. [Технологии](#Технологии)
3. [Подготовка к работе](#Подготовка-к-работе-и-использование)
4. [ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ](#ОТКАЗ-ОТ-ОТВЕТСТВЕННОСТИ)

## Особенности
Основные возможности этого бота включают:
  + Управление запуском
  + Поиск по идентификатору приложения
  + Регистрация времени последней проверки разрешения на запуск приложения
  + Авторизация по паре логин-пароль
  + Автоматическое добавление приложения после отправки запроса от него


## Технологии

| Технология | Описание                                                    |
|------------|-------------------------------------------------------------|
| aiogram    | Библиотека для веб- и нативных пользовательских интерфейсов |
| Redis      | in-memory key-value database, кэш и брокер сообщений        |
| FastAPI    | Высокопроизводительный веб-фреймворк для создания API       |
| SQLAlchemy | Python SQL toolkit and ORM                                  |

### Запуск на системе

1. Установите [Python 3.10+](https://python.org/)  
2. Установите [Redis](https://redis.io/)  
3. Загрузите исходный код проекта  
4. Создайте виртуальное окружение:
   - На Linux:
     ```bash
     python3 -m venv .venv
     ```
   - На Windows:
     ```bash
     python -m venv .venv
     ```
5. Активируйте виртуальное окружение:
   - На Linux:
     ```bash
     source .venv/bin/activate
     ```
   - На Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - На Windows (cmd):
     ```cmd
     .venv\Scripts\activate.bat
     ```
6. Установите зависимости проекта:
   ```bash
   pip install -r telegram_bot/requirements.txt
   ```
7. Скопируйте файл `env.example` в `telegram_bot/.env` и отредактируйте файл `.env`.  
8. Перейдите в каталог `telegram_bot` и запустите утилиту управления:
   - На Linux:
     ```bash
     python3 manage.py
     ```
   - На Windows:
     ```cmd
     python manage.py
     ```
   Это запустит утилиту, в которой можно создать пользователя.  
9. Запустите бота из каталога `telegram_bot`:
   - На Linux:
     ```bash
     python3 bot.py
     ```
   - На Windows:
     ```cmd
     python bot.py
     ```

### Запуск с использованием Docker

1. Установите [Docker](https://docker.com)  
2. Скопируйте файл `env.example` в `.env` и отредактируйте его при необходимости.  
3. Создайте контейнер Redis, выполнив следующую команду:
   ```bash
   make storage
   ```
4. Запустите утилиту управления в контейнере, выполнив:
   ```bash
   make manage
   ```
   Это запустит утилиту, в которой можно добавить пользователя.  
5. Запустите бота в контейнере, выполнив:
   ```bash
   make up
   ```

В обоих случаях бот начинает слушать LISTEN_HOST:LISTEN_PORT из файла `.env`.

Чтобы приложение проверяло право на выполнение, необходимо отправить HTTP-запрос следующего формата:
```
Тип запроса: GET
Путь: /
Заголовки:
"APP_ID_HEADER": ‘com.example.app’.
```

Заголовок, который ожидает бот, настраивается в `.env`.  
Если ответом будет строка, указанная в `OK_RESPONSE`, ваше приложение может продолжить выполнение. Если будет получена строка `BLOCKED_RESPONSE`, приложение должно завершить работу.

`OK_RESPONSE`, `BLOCKED_RESPONSE`, `APP_ID_HEADER` настраиваются в файле `.env`.

Для использования в продакшене бот должен быть развернут за nginx.

## ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ
Пользователь этого программного обеспечения подтверждает, что оно предоставляется "как есть", без каких-либо явных или неявных гарантий. 
Разработчик программного обеспечения не несет ответственности за любые прямые или косвенные финансовые потери, возникшие в результате использования данного программного обеспечения. 
Пользователь несет полную ответственность за свои действия и решения, связанные с использованием программного обеспечения.