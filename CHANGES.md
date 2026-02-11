# Изменения: Интеграция с MongoDB и PostgreSQL

## Сводка изменений

Добавлена полная интеграция с базами данных для получения реальных данных пользователей и сохранения сгенерированных планов.

---

## 📁 Новые файлы

### 1. `utils/data_loader.py`
**Назначение**: Удобный загрузчик данных пользователя из всех источников

**Методы**:
- `load_all_data(user_id)` - загрузить все данные пользователя одним вызовом
- `get_user_profile(user_id)` - профиль из PostgreSQL
- `get_questionnaire(user_id)` - анкета из активного userblock (MongoDB)
- `get_latest_inbody(user_id)` - последний InBody тест (PostgreSQL)
- `get_checkins_history(user_id, days=90)` - посещения за N дней (PostgreSQL)
- `get_marathons_history(user_id, limit=5)` - история марафонов (MongoDB)
- `get_heropass(user_id)` - активный HeroPass с клубом (MongoDB)

**Использование**:
```python
from utils.data_loader import UserDataLoader

user_data = UserDataLoader.load_all_data('507f1f77bcf86cd799439011')
```

---

### 2. `example_usage_with_db.py`
**Назначение**: Пример работы с реальными данными из БД

**Функции**:
- Загрузка данных пользователя из MongoDB и PostgreSQL
- Генерация плана на основе реальных данных
- Сохранение результата в userblock и в файл
- Интерактивный режим для тестирования

**Использование**:
```bash
# С указанием user_id
python example_usage_with_db.py 507f1f77bcf86cd799439011

# Интерактивный режим
python example_usage_with_db.py
```

---

### 3. `explore_postgres.py`
**Назначение**: Утилита для исследования структуры таблиц PostgreSQL

**Функции**:
- Показывает структуру таблиц (колонки, типы данных)
- Выводит примеры записей
- Помогает проверить правильность названий полей

**Использование**:
```bash
python explore_postgres.py
```

**Проверяемые таблицы**:
- `checkins` - история посещений
- `assessments` - оценки
- `userinbodytests` - InBody тесты
- `users` - пользователи

---

## ✏️ Изменённые файлы

### 1. `db/mongo_connection.py`
**Добавлено**:

**Коллекции**:
- `user_heropasses()` - коллекция HeroPass
- `user_marathons()` - коллекция марафонов
- `programsets()` - коллекция программ

**Методы для HeroPass**:
- `get_active_heropass(user_id)` - получить активный HeroPass
- `get_user_heropasses(user_id)` - получить все HeroPass пользователя

**Методы для марафонов**:
- `get_user_marathons(user_id, limit=5)` - история марафонов
- `get_completed_marathons(user_id)` - только завершённые марафоны

**Методы для programsets**:
- `get_all_program_types()` - все уникальные типы программ
- `get_programsets_by_type(program_type)` - программы определённого типа

**Вспомогательные методы**:
- `get_user_club_info(user_id)` - получить club_id и club_name через HeroPass

**Важно**: Все методы принимают `user_id` как str или ObjectId и автоматически конвертируют.

---

### 2. `db/postgres_connection.py`
**Добавлено**:

**Методы для InBody**:
- `get_latest_inbody(user_id)` - последний InBody тест пользователя
- `get_user_inbody_history(user_id, limit=5)` - история InBody тестов

**Особенности**:
- Использует поле `"user"` (в кавычках, т.к. это зарезервированное слово в PostgreSQL)
- Сортировка по `testdate DESC` для получения последних тестов

---

### 3. `generators/club_filter.py`
**Изменено**:

**Метод `get_user_club_data()`**:
- Раскомментирован запрос к MongoDB
- Использует `MongoConnection.get_user_club_info(user_id)` для получения клуба
- Обработка ошибок с fallback на "все доступно"
- Упрощённая логика с использованием нового helper метода

**До**:
```python
# TODO: В продакшене здесь будет запрос к MongoDB
# Закомментированный код
```

**После**:
```python
try:
    from db import MongoConnection
    club_info = MongoConnection.get_user_club_info(user_id)
    if club_info and club_info.get('club_name'):
        club_name = club_info['club_name']
        if club_name in CLUB_STRUCTURE:
            return self._build_club_data(club_name)
except Exception as e:
    logging.warning(f"Ошибка при получении данных клуба: {e}")
```

---

### 4. `README.md`
**Добавлено**:

**Секция "Установка зависимостей"**:
- Добавлены `psycopg2` и `pymongo` в список зависимостей

**Секция "Настройка подключений к БД"**:
- Переменные окружения для MongoDB
- Переменные окружения для PostgreSQL
- Пример `.env` файла

**Секция "Запуск примеров"**:
- Тестирование без БД (`example_usage.py`)
- Работа с реальными данными (`example_usage_with_db.py`)
- Утилиты для проверки БД (`explore_postgres.py`, `explore_structure.py`)

**Секция "Работа с реальными данными из БД"**:
- Пример использования `UserDataLoader`
- Загрузка данных из БД
- Сохранение результата в userblock
- Описание всех методов UserDataLoader

---

## 🔧 Технические детали

### Названия полей в таблицах

**PostgreSQL**:
- `checkins.user_id` - ID пользователя (INTEGER)
- `assessments.user_id` - ID пользователя (INTEGER)
- `userinbodytests."user"` - ID пользователя (INTEGER, в кавычках)
- `users.id` - ID пользователя (INTEGER, PRIMARY KEY)

**MongoDB**:
- `userblocks.user` - ObjectId пользователя
- `userheropasses.user` - ObjectId пользователя
- `usermarathons.user` - ObjectId пользователя
- `clubs._id` - ObjectId клуба
- `clubs.name` - Название клуба (string)

### Обработка ошибок

Все методы работы с БД имеют обработку ошибок:
- Try-catch блоки для каждого запроса
- Логирование ошибок через `logging.warning()`
- Fallback на безопасные значения (None, [], {})
- Graceful degradation при недоступности БД

### Автоконвертация типов

`MongoConnection` методы автоматически конвертируют:
- `str` → `ObjectId` для user_id
- Возвращают данные в удобном формате

---

## 📝 Примеры использования

### Базовый пример с данными из БД

```python
from generators.plan_generator import RecommendedPlanGenerator
from utils.data_loader import UserDataLoader

# Загрузить данные
user_id = '507f1f77bcf86cd799439011'
user_data = UserDataLoader.load_all_data(user_id)

# Проверить анкету
if not user_data['questionnaire']:
    print("Анкета не найдена!")
    exit()

# Генерация
generator = RecommendedPlanGenerator()
result = generator.generate(
    user_id=user_id,
    **{k: v for k, v in user_data.items() if k != 'user_profile'}
)

# Сохранение в MongoDB
from db import MongoConnection
userblock = MongoConnection.get_active_user_block(user_id)
MongoConnection.update_user_block(
    str(userblock['_id']),
    {
        'recommendedPlan': result['recommendedPlan'],
        'tasksProgress': result['tasksProgress']
    }
)
```

### Проверка данных пользователя

```python
from utils.data_loader import UserDataLoader

user_id = '507f1f77bcf86cd799439011'

# Проверка отдельных компонентов
questionnaire = UserDataLoader.get_questionnaire(user_id)
print(f"Анкета: {questionnaire is not None}")

inbody = UserDataLoader.get_latest_inbody(user_id)
print(f"InBody: {inbody is not None}")

checkins = UserDataLoader.get_checkins_history(user_id)
print(f"Посещения: {len(checkins)} записей")

marathons = UserDataLoader.get_marathons_history(user_id)
print(f"Марафоны: {len(marathons)} записей")

heropass = UserDataLoader.get_heropass(user_id)
print(f"HeroPass: {heropass.get('club_name') if heropass else 'нет'}")
```

---

## ✅ Чек-лист интеграции

- [x] Добавлены методы в `MongoConnection` для HeroPass
- [x] Добавлены методы в `MongoConnection` для марафонов
- [x] Добавлены методы в `MongoConnection` для programsets
- [x] Добавлен helper метод `get_user_club_info()`
- [x] Добавлены методы в `PostgresConnection` для InBody
- [x] Исправлен `club_filter.py` для работы с реальными данными
- [x] Создан `UserDataLoader` для удобной загрузки данных
- [x] Создан `example_usage_with_db.py` для демонстрации
- [x] Создан `explore_postgres.py` для проверки структуры БД
- [x] Обновлён `README.md` с информацией о работе с БД
- [x] Документированы все методы и функции
- [x] Добавлена обработка ошибок во всех запросах к БД

---

## 🚀 Следующие шаги

1. **Тестирование**: Запустить `explore_postgres.py` и `explore_structure.py` для проверки структуры БД
2. **Проверка полей**: Убедиться что названия полей в таблицах соответствуют коду
3. **Тестирование с реальными данными**: Запустить `example_usage_with_db.py` с реальным user_id
4. **Корректировка**: Если структура таблиц отличается, обновить запросы в соответствующих методах

---

## 📞 Поддержка

При возникновении проблем с БД:
1. Проверьте `.env` файл (правильность подключений)
2. Запустите `explore_postgres.py` для проверки PostgreSQL
3. Запустите `explore_structure.py` для проверки MongoDB
4. Проверьте логи в консоли (logging.warning выводит ошибки)
