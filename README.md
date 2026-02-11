# Система генерации персонализированных планов тренировок Hero Fitness

LLM-центричная система для генерации индивидуальных recommendedPlan и tasksProgress на основе анкеты пользователя, InBody данных, истории посещений и марафонов.

## 🎯 Возможности

- **Персонализация**: Gemini API создаёт уникальный план под каждого атлета
- **Учёт истории**: Анализ реальной частоты посещений и успешности марафонов
- **Фильтрация по клубу**: Только доступные программы на основе зон клуба
- **Валидация**: Проверка правил восстановления мышц и корректности плана
- **Edge cases**: Обработка ограничений здоровья, перерывов, возраста через промпт

## 📁 Структура проекта

```
blocks_custom_programs/
├── generators/
│   ├── plan_generator.py          # Главный оркестратор с Gemini API
│   ├── user_analyzer.py           # Анализ профиля пользователя
│   ├── history_analyzer.py        # Анализ истории посещений/марафонов
│   ├── club_filter.py             # Фильтрация по зонам клуба
│   └── tasks_generator.py         # Генерация tasksProgress
├── rules/
│   ├── recovery_rules.py          # Правила восстановления мышц
│   ├── goal_mappings.py           # Маппинг цель→типы программ
│   └── club_zones.py              # Структура клубов и зон
├── models/
│   ├── user_profile.py            # Dataclass для профиля
│   └── plan_structure.py          # Dataclasses для плана
├── utils/
│   ├── prompt_builder.py          # Построение промптов для LLM
│   ├── plan_validator.py          # Валидация сгенерированного плана
│   └── pattern_loader.py          # Загрузка паттернов из контекста
├── Контекст Путъ Атлета.md        # Примеры паттернов (Burn, Fit Body, Legs, Build, Athlete)
├── Контекст Программы.md          # Структура клубов и программ
├── example_usage.py               # Пример использования
└── .env                           # Конфигурация (GEMINI_API_KEY)
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install google-generativeai python-dotenv psycopg2 pymongo
```

### 2. Настройка подключений к базам данных

Создайте файл `.env` в корне проекта:

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB
MONGO_CONNECTION_STRING=mongodb://localhost:27017
MONGO_DB=hero-app-prod

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=hj_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

Получить Gemini API ключ: https://aistudio.google.com/app/apikey

### 3. Запуск примеров

**Тестирование без БД** (с моковыми данными):
```bash
python example_usage.py
```

**Работа с реальными данными из БД**:
```bash
# Запуск для конкретного пользователя
python example_usage_with_db.py <user_id>

# Интерактивный режим
python example_usage_with_db.py
```

**Проверка структуры БД**:
```bash
# PostgreSQL таблицы
python explore_postgres.py

# MongoDB коллекции
python explore_structure.py

# Programsets
python explore_programsets.py
```

## 📖 Использование

### Базовый пример

```python
from generators.plan_generator import RecommendedPlanGenerator

# Инициализация
generator = RecommendedPlanGenerator()

# Данные анкеты
questionnaire = {
    'gender': 'male',
    'age': 28,
    'goal': 'похудение',
    'focus': ['выносливость', 'ноги'],
    'experience': 'любитель',
    'current_break': 30,
    'health_restrictions': []
}

# Генерация плана
result = generator.generate(
    user_id='user_123',
    questionnaire_data=questionnaire,
    heropass_data={'club_name': 'Europa City'}
)

# Результат
print(f"Тренировок: {len(result['recommendedPlan'])}")
print(f"Задач: {len(result['tasksProgress'])}")
```

### С полными данными

```python
result = generator.generate(
    user_id='user_123',
    questionnaire_data=questionnaire,
    inbody_data=inbody_data,           # Данные InBody
    checkins_data=checkins_list,       # История посещений (3 месяца)
    marathons_data=marathons_list,     # История марафонов
    heropass_data=heropass_data,       # HeroPass с club_id
    max_attempts=3                     # Попытки генерации
)
```

### Работа с реальными данными из БД

Используйте `UserDataLoader` для автоматической загрузки данных:

```python
from generators.plan_generator import RecommendedPlanGenerator
from utils.data_loader import UserDataLoader

# Загрузить все данные пользователя из MongoDB и PostgreSQL
user_data = UserDataLoader.load_all_data(user_id='507f1f77bcf86cd799439011')

# Проверить что анкета заполнена
if user_data['questionnaire']:
    # Генерация плана с реальными данными
    generator = RecommendedPlanGenerator()
    result = generator.generate(
        user_id=user_id,
        questionnaire_data=user_data['questionnaire'],
        inbody_data=user_data['inbody_data'],
        checkins_data=user_data['checkins_data'],
        marathons_data=user_data['marathons_data'],
        heropass_data=user_data['heropass_data']
    )

    # Сохранить план в userblock
    from db import MongoConnection
    userblock = MongoConnection.get_active_user_block(user_id)
    if userblock:
        MongoConnection.update_user_block(
            str(userblock['_id']),
            {
                'recommendedPlan': result['recommendedPlan'],
                'tasksProgress': result['tasksProgress']
            }
        )
```

**Методы UserDataLoader**:
- `load_all_data(user_id)` - загрузить все данные пользователя
- `get_questionnaire(user_id)` - анкета из активного userblock
- `get_latest_inbody(user_id)` - последний InBody тест из PostgreSQL
- `get_checkins_history(user_id, days=90)` - посещения за N дней из PostgreSQL
- `get_marathons_history(user_id, limit=5)` - история марафонов из MongoDB
- `get_heropass(user_id)` - активный HeroPass с названием клуба

## 📊 Структура входных данных

### Анкета (questionnaire)

```python
{
    'gender': 'male',                    # male/female
    'age': 28,
    'height': 178,                       # см
    'weight': 80,                        # кг
    'current_form': 'среднее',           # худощавое/среднее/плотное/спортивное/полное
    'goal': 'похудение',                 # похудение/масса/рельеф/здоровье/поддержание
    'focus': ['выносливость', 'ноги'],   # верх_тела/ноги/выносливость/баланс
    'experience': 'любитель',            # новичок/любитель/профи
    'current_break': 30,                 # дней без тренировок
    'health_restrictions': []            # протрузия/грыжа, травмы_суставов, кардио_ограничения
}
```

### InBody данные (опционально)

```python
{
    'body_fat_percentage': 18.5,
    'muscle_mass': 35.2,
    'bmi': 25.2,
    'visceral_fat': 8
}
```

### История посещений (опционально)

```python
[
    {'date': '2024-01-15T10:00:00Z', ...},
    {'date': '2024-01-17T18:00:00Z', ...}
]
```

### История марафонов (опционально)

```python
[
    {
        'status': 'completed',
        'medal': 'gold',
        'attendance_rate': 0.85
    }
]
```

## 📤 Структура выходных данных

### recommendedPlan

```json
[
  {
    "text": "Выполни тренировку BootCamp",
    "week": 1,
    "day": 1,
    "programSetTypes": ["bootcamp", "metcon"],
    "part": 1
  }
]
```

### tasksProgress

```json
[
  {
    "text": "Выполни 12 тренировок BootCamp",
    "programSetTypes": ["bootcamp"],
    "part": 1,
    "target": 12,
    "done": 0,
    "week": 1
  }
]
```

### metadata

```json
{
  "user_id": "user_123",
  "frequency": 4,
  "progression_level": "intermediate",
  "goal": "похудение",
  "club_name": "Europa City",
  "total_workouts": 32,
  "total_tasks": 8
}
```

## ⚙️ Алгоритм работы

1. **Анализ профиля** - определение частоты (3-5 тренировок/неделю), уровня опыта
2. **Фильтрация по клубу** - только доступные программы на основе зон клуба
3. **Загрузка паттернов** - примеры из контекстного файла (Burn, Fit Body, Legs, Build, Athlete)
4. **Построение промпта** - с учётом edge cases (ограничения, перерывы, возраст)
5. **Генерация LLM** - Gemini API создаёт индивидуальный план
6. **Валидация** - проверка восстановления, частоты, структуры (до 3 попыток)
7. **Генерация задач** - автоматическое создание tasksProgress из плана

## 🎯 Правила генерации

### Частота тренировок (3-5 в неделю)

- **Базовая**: 3 (новичок)
- **+1**: любитель
- **+2**: профи
- **+1**: цель масса/рельеф
- **+1**: реальная частота 4+ раза/неделю
- **+1**: успешные марафоны с золотом
- **-1**: перерыв >3 месяцев
- **-1**: ограничения здоровья

### Правила восстановления

- **Push/Pull/Legs**: 2 дня между тренировками
- **Bootcamp/Metcon**: 1 день между тренировками
- **Full Body**: 1-2 дня в зависимости от интенсивности

### Распределение по дням

- **3 тренировки**: ПН(1), СР(3), ПТ(5)
- **4 тренировки**: ПН(1), ВТ(2), ЧТ(4), ПТ(5)
- **5 тренировок**: ПН(1), ВТ(2), СР(3), ПТ(5), СБ(6)

### Прогрессия

- **Part 1 (недели 1-4)**: Базовый уровень интенсивности
- **Part 2 (недели 5-8)**: Повышенная интенсивность

## 🏋️ Клубы и зоны

Система учитывает реальную структуру клубов:

- **Nurly-Orda**: FFB/Upper, Legs, Bootcamp
- **Europa City**: FFB/Upper, Legs, Metcon, Bootcamp, Mind Body
- **Colibri**: FFB/Upper, Legs, Metcon, Bootcamp
- **Promenade**: FFB/Upper, Legs, Metcon, Bootcamp
- **Villa**: Full Body, Reshape, Bootcamp
- **HJ 4You**: FFB/Upper, Legs, Metcon, Bootcamp, Reshape, Assessment

## 🧪 Тестирование

```bash
# Запуск примера
python example_usage.py

# Unit тесты (TODO)
pytest tests/

# Integration тесты (TODO)
pytest tests/integration/
```

## 📝 TODO

- [ ] Unit тесты для всех модулей
- [ ] Integration тесты с реальными данными
- [ ] Интеграция с MongoDB/PostgreSQL
- [ ] Парсер CSV анкет
- [ ] Логирование и мониторинг LLM запросов
- [ ] Обработка ошибок Gemini API (rate limits, timeouts)
- [ ] Кэширование паттернов
- [ ] API эндпоинт для генерации планов

## 🤝 Вклад

1. Форк репозитория
2. Создание ветки (`git checkout -b feature/amazing-feature`)
3. Коммит изменений (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Pull Request

## 📄 Лицензия

Proprietary - Hero Fitness

## 👥 Контакты

Hero Fitness Team - [info@herofitness.kz](mailto:info@herofitness.kz)
