# Бот для бронирования дат поставок

## Как пользоваться

### Запуск

1. Создать rdp-подключение и авторизваться на сервере, на котором установлен бот (далее "сервер"):

На Windows:

a. Пуск -> Подключение к удалённому рабочему столу

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-36-26.jpg?raw=true)

b. Ввести ip-адрес сервера, нажать "Показать параметры".

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-01.jpg?raw=true)

c. Ввести имя пользователя (по умолчанию - root). Поставить галку "Разрешить мне сохранять учётные данные". Нажать "Подключить".

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-10.jpg?raw=true)

d. Ввести пароль от учётной записи, нажать "Ok".

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-17.jpg?raw=true)

2. На удалённом рабочем столе открыть терминал.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-23.jpg?raw=true)

3. Запустить бота, последовательно выполнив через командную строку указанные команды:

Для копирования/вставки в окне терминала используются комбинации `Ctrl+Shift+C`/`Ctrl+Shift+V`.

- включение режима bash
```
bash
```
- переход в директорию с ботом
```
cd git/booking_delivery_date_bot
```
- активация виртуального окружения
```
source venv/bin/activate
```
- запуск бота в фоновом режиме с игнорированием завершения сеанса пользователя
```
nohup python3 main.py &
```

Далее можно закрыть окно удалённого рабочего стола, бот будет работать удалённо.

### Редактирование настроек поиска дат для бронирования

Бот собирает параметры поставок из [строго определённой таблицы](https://docs.google.com/spreadsheets/d/1fjCuy2j6gikIDPR5HZvEThrT3BLyr-0iHmx7Ek4-VnY/edit?usp=sharing).
![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-44.jpg?raw=true)

Важно отметить, что таблица имеет конкретный формат, который ни в коем случае нельзя менять по своему усмотрению - это приведёт неполадкам в работе бота. Так же важно учитывать правильный формат и корректность самих данных поставки - записи с несуществующим номером поставки или временем сборки "два дня" будут проигнорированы.

Описание полей таблицы:

`Номер поставки` - идентификатор поставки в [личном кабинете](https://seller.ozon.ru/app/supply/orders?filter=SupplyPreparation). Может содержать только цифры.

`Начало периода для поиска даты отгрузки` - желаемая дата отгрузки. По возможности, для отгрузки будет выбрана эта дата, при условии достаточного времени на сборку и наличия соответствующих таймслотов в [личном кабинете](https://seller.ozon.ru/app/supply/orders?filter=SupplyPreparation). Строго в формате ДД.ММ.ГГГГ, например: 09.11.2022.

`Конец периода для поиска даты отгрузки` - самая поздняя дата отгрузки. Временно не используется.

`Время сборки заказа в полных днях` - время, необходимое на сборку поставки. Это значение учитывается при поиске слота поставки. Если разница между текущей датой и желаемой датой поставки составляет меньше этого значения, желаемая дата поставки будет скорректирована в большую сторону (без отражения в таблице).

`Текущая дата отправки заказа` - заполняется автоматически при работе бота при нахождении слота с более подходящей датой. 

`Имя аккаунта` - аккаунт, для которого производится поиск слота поставки. На текущий момент поиск ведётся по одному конкретному аккаунту (задаётся в файле конфигурации бота). Заполнять строго в соответствии с именем аккаунта в ЛК.

`Дата найдена` - флаг, указывающий на завершённость поиска по данной поставке. Автоматически проставляется "1" в случае, если забронирована либо изначально желаемая дата поставки, либо скорректированная с учётом времени сборки поставки. При значении "1" бот будет игнорировать данную поставку, в противном случае ("0" или пустая ячейка) - проведёт поиск слота поставки.

### Ограничения доступа

Список пользователей, имеющих доступ к таблице устанавливается с помощью стандартного интерфейса Google Spreadsheet.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-50.jpg?raw=true)

Удалять из списка пользователя с почтовым доменом `...gserviseaccount.com` строго запрещено - это сервисный аккаунт, через который бот взаимодействует с таблицей.

![](https://github.com/smalldirtybird/booking_delivery_date_bot/blob/main/docs/photo_2022-10-19_16-37-56.jpg?raw=true)
