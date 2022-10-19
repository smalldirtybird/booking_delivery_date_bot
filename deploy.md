# Инструкция по установке бота

В данной инструкции описаны шаги, необходимые для установки и запуска бота на сервере под управлением Linux Ubuntu 22.04.

### Примечания:

- в данной инструкции приведены команды для командной строки Linux. Для работы с ними в Windows можно использовать [подсистему Linux](https://g-ek.com/kak-zapustit-bash-v-windows-10) или [Windows PowerShell](https://docs.microsoft.com/ru-ru/powershell/scripting/overview?view=powershell-7.2);
- в примерах команд в фигурных скобках `{}` указаны переменные значения, которые необходимо заменить на фактические. Все параметры команд вводятся БЕЗ фигурных скобок;
- в процессе выполнения приведённых команд система может запрашивать подтверждение выполняемых действий. В этом случае нужно согласиться, нажав `Y`, потом `Enter`;
- если при выполнении команды терминал отвечает фразой "... not found", одним из вариантов решения может быть команда `bash` и повтор ввода. 

## Подключение к серверу, создание пользователя и предоставление прав

### Если у пользователя нет учётной записи на сервере

1. Открыть терминал и выполнить команду:
```
ssh root@{server_ip_address}
```
Здесь и далее: {server_ip_address} - ip-адрес сервера.

По требованию сервера ввести пароль.

2. Создать нового пользователя с домашней директорией:
```
useradd -m {username}
```
Здесь и далее: {username} - имя пользователя.

3. Присвоить пользователю пароль:
```
passwd {username}
```
Терминал попросит ввести, а затем подтвердить пароль пользователя.

4. Добавить пользователя в группу sudo:
```
usermod -aG sudo {username}
```

5. Выйти из сессии:
```
exit
```
и зайти на сервер под только что созданным пользователем:
```
ssh {user}@{server_ip_address}
```
По требованию сервера ввести пароль.

### Если у пользователя уже есть учётная запись на сервере, но он не добавлен в группу sudo (или это точно неизвестно):

1. Открыть терминал и выполнить команду:
```
ssh root@{server_ip_address}
```
Здесь и далее: {server_ip_address} - ip-адрес сервера.
По требованию сервера ввести пароль.

2. Добавить пользователя в группу sudo:
```
usermod -aG sudo {username}
```
Здесь и далее: {username} - имя пользователя.

3. Выйти из сессии:
```
exit
```
и зайти на сервер под только что созданным пользователем:
```
ssh {user}@{server_ip_address}
```
По требованию сервера ввести пароль.

### Если у пользователя уже есть учётная запись на сервере и он добавлен в группу sudo

Открыть терминал и выполнить команду:
```
ssh {user}@{server_ip_address}
```
где {user} - имя пользователя, {server_ip_address} - ip-адрес сервера.
По требованию сервера ввести пароль.

## Установка ПО

1. Обновить списки пакетов в системе:
```
sudo apt update
```

2. Обновить пакеты до последней версии:
```
sudo apt upgrade
```
Система может спросить о перезагрузке ряда сервисов - согласиться и перезапустить.

3. Приложение написан на Python3.10, установить его командой:
```
sudo apt install python3.10
```

4. Установить менеджер загрузки пакетов pip:
```
sudo apt install python3-pip
```

5. Все файлы приложения размещены на удалённом репозитории Git, установить пакет для работы с ним:
```
sudo apt install git
```

6. Установить средство работы с виртуальным окружением virtualenv:
```
sudo apt install python3-virtualenv
```

7. Приложение использует браузер Mozilla Firefox, который нередко устанавливается вместе с Ubuntu как snap. Для работы бота такой вариант не подходит, необходимо установить его в классическом режиме, для этого необходимо последовательно выполнить шаги, приведённые в [этой статье](https://fostips.com/ubuntu-21-10-two-firefox-remove-snap/).

8. Приложение использует сервисы Gmail и Google Spreadsheets. Необходимо использовать аккаунт Google с почтой, привязанной к OzonID бота, либо создать новый, если такового нет. Далее последовательно выполнить следующие шаги:

8.1 [Создать проект в Google Cloud](https://console.cloud.google.com/). Вверху страницы вызвать выпадающее меню выбора проекта и нажать `New project`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-12-52.jpg?raw=true)

Ввести имя проекта и нажать "Create", далее выбрать его в выпадающем меню.

8.2 В [консоли проекта](https://console.cloud.google.com/) перейти во вкладку `APIs & Services/Enabled APIs & services`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-03.jpg?raw=true)

Нажать `ENABLE APIS AND SERVISES`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-12.jpg?raw=true)

Через поисковую строку найти `Gmail API`, перейти его на страницу и нажать `ENABLE`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-17.jpg?raw=true)
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-24.jpg?raw=true)

Аналогичным образом разрешить Google Sheet API и Google Drive API.

8.3 На вкладке [APIs & Services](https://console.cloud.google.com/apis/) перейти к пункту `Credentials`, нажать `CREATE CREDENTIALS` и выбрать `OAuth clientID`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-35.jpg?raw=true)

Нажать `CONFIGURE CONSENT SCREEN`, выбрать User Type `External` и нажать `Create`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-39.jpg?raw=true)
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-43.jpg?raw=true)

Заполнить обязательные поля, отмеченные звё1здочкой `*`, нажать `SAVE AND CONTINUE`.

Повторить первый шаг данного пункта - дойти до вкладки `Create OAuth client ID`. Далее выбрать тип приложения `Desktop app` и нажать `Create`.
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-51.jpg?raw=true)

Появится всплывающее окно с секретными ключами с кнопкой `DOWNLOAD JSON`, нажать её и сохранить как `google_credentials.json`.
Далее нажать `OK`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-13-58.jpg?raw=true)

8.4 На той же странице в области `Service Accounts` нажать на `Manage service accounts`, далее `CREATE SERVICE ACCOUNT`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-14-04.jpg?raw=true)
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-14-17.jpg?raw=true)

Указать id аккаунта (на свой выбор) и нажать `DONE`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-14-22.jpg?raw=true)

В области `Service accounts for project...` нажать на email только что созданного аккаунта, перейти на вкладку `KEYS`, нажать `ADD KEY` и выбрать `Create new key`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-14-27.jpg?raw=true)
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-14-34.jpg?raw=true)

Во всплывающем окне выбрать `JSON`, нажать `CREATE`. Полученный файл сохранить как `spreadsheet_credentials.json`. Далее скопировать email из `Service acoounts for project`. 
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-15-08.jpg?raw=true)

8.5 [Создать новую таблицу](https://docs.google.com/spreadsheets/u/0/) со следующей структурой:
`Номер поставки, цифры`	`Начало периода для поиска даты отгрузки, ДД.ММ.ГГГГ`	`Конец периода для поиска даты отгрузки, ДД.ММ.ГГГГ`	`Время сборки заказа в полных днях, цифры`	`Текущая дата отправки заказа, заполняется автоматически`	`Имя аккаунта`	`Дата найдена, заполняется автоматически, 1 - да, 0 - нет`
В только что созданной таблице нажать `Настройки Доступа` и добавить скопированный email сервисного аккаунта как редактора. Нажать`Готово`.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_20-15-14.jpg?raw=true)

9. Для первого запуска боту потребуется графический интерфейс. Если он не установлен на сервере, необходимо установить его, следуя [инструкции](https://help.reg.ru/support/servery-vps/oblachnyye-servery/ustanovka-programmnogo-obespecheniya/graficheskiye-obolochki-ubuntu).

10. Для работы необходим профиль Firefox. Можно использовать существующий, скопировав его в удобное место на сервере, или создать новый непосредственно из сервера после установки графической оболочки. По умолчанию профили пользователей Firefox в Ubuntu лежать по следующему адресу:
`/home/{username}/.mozilla/firefox/`

11. Для мониторинга и оповещения о работе бота используется мессенджер Telegram. Необходимо создать TG-бота, который будет интегрирован с приложением и отправлять оповещения в указанный чат. Для этого нужно:

11.1 В Telegram написать [@BotFather](https://t.me/BotFather), используя команду `/newbot` и следуя инструкциям создать нового бота. В итоге в чате появится сообщение, содержащее токен бота - его нужно сохранить.

11.2 Если бот должен отправлять сообщения в публичный чат или канал - добавить туда TG бота и в настройках чата разрешить ему отправлять сообщения.

11.3 Если бот должен отправлять сообщения в личные сообщения конкретному пользователю, пользователь перед первым запуском должен запустить чат с ботом, написав ему любое сообщение.

## Установка файлов приложения

1. Перейти в директорию Git на сервере командой
```
cd ~/git
```

2. Скачать репозиторий на сервер:
```
git clone https://github.com/smalldirtybird/booking_delivery_date_bot.git
```

3. Проверить результат:
```
ls
```

Отобразится список папок с репозиториями, в котором должна присутствовать `booking_delivery_date_bot`.

## Настройка приложения

1. Перейти в директорию с проектом:
```
cd ~/git/booking_delivery_date_bot
```
и установить виртуальное окружение командой
```
virtualenv -p /usr/bin/python3.10 --pip 22.2.2 venv

```

Далее активировать окружение:
```
source venv/bin/activate
```
и установить библиотеки:
```
pip install -r requirements.txt
```
Отдельной командой установить google-api-client:
```
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

2. Создать файл .env для переменных окружения с помощью встроенного текстового редактора nano:
```
nano .env
```

В файл внести следующие строки:
``` python
GOOGLE_APPLICATION_CREDENTIALS = {путь к файлу google_credentials.json}
GOOGLE_SPREADSHEET_CREDENTIALS = {путь к файлу spreadsheet_credentials.json
TABLE_NAME = {название таблицы, созданной в п. 8.5}
SHEET_NAME = {название листа таблицы из п. 8.5}
ACCOUNT_NAME = {имя аккаунта для бронирования дат поставки}
FIREFOX_PROFILE_PATH = {путь к папке профиля Firefox}
OZON_LOGIN_EMAIL = {адрес Gmail, привязанный к OzonID}
ACTION_DELAY_FLOOR = {нижний порог задержки между действиями бота, сек.}
ACTION_DELAY_CEIL = {верхний порог задержки между действиями бота, сек.}
SLEEP_TIME_MINUTES = {время между перезапусками бота}
TELEGRAM_BOT_TOKEN = {токен Telegram-бота для оповещений}
TELEGRAM_CHAT_ID = {id чата, в который бот должен отправлять сообщения.}
```
3. Первый запуск.

Первый запуск необходимо производить с использованием графического интерфейса. Бот выведет на экран страницу авторизации аккаунта Google, в котором нужно одобрить все запрашиваемые им разрешения от имени аккаунта, используемого в п.8. После сообщения об успешной авторизации, приложение необходимо полностью перезапустить.
