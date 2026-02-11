# Интеграция с базами данных - Сводка

## ✅ Что сделано

### 1. Обновлены запросы в PostgreSQL

**Файл**: `db/postgres_connection.py`

Все методы обновлены для работы с реальными views и таблицами:

| Метод | Источник | Описание |
|-------|----------|----------|
| `get_user_checkins()` | `raw.usercheckin` + JOIN | История посещений с типом программы |
| `get_latest_inbody()` | `ris.v_user_inbody_tests` | Последний InBody тест |
| `get_user_inbody_history()` | `ris.v_user_inbody_tests` | История InBody тестов |
| `get_user_profile()` | `ris.core_user` | Профиль пользователя |
| `get_user_strength_measurements()` | `ris.v_user_strength_measurements` | Результаты 1RepMax |
| `get_user_heropass()` | `ris.v_user_heropass` | Активный HeroPass |
| `get_user_marathons()` | `ris.v_user_marathons` | История марафонов |

### 2. Обновлён UserDataLoader

**Файл**: `utils/data_loader.py`

Все методы обновлены для правильного маппинга полей:

- ✅ **InBody**: `pbf` → `body_fat_percentage`, `smm` → `muscle_mass`, `fs` → `fitness_score`, `wt` → `weight`
- ✅ **Checkins**: Извлекает `program_type` для анализа истории
- ✅ **Marathons**: Рассчитывает `attendance_rate` и определяет `status`
- ✅ **HeroPass**: Сначала PostgreSQL, затем fallback на MongoDB
- ✅ Все `user_id` - строки (MongoDB ObjectId)

### 3. Созданы утилиты для проверки

**check_db_structure.py** - Проверяет структуру всех views/таблиц:
```bash
python check_db_structure.py
```

**test_data_loader.py** - Тестирует загрузку данных для пользователя:
```bash
python test_data_loader.py <user_id>
```

---

## 🎯 Ключевые находки

### 1. User ID - это строка везде
Во всех таблицах PostgreSQL `user_id` имеет тип VARCHAR и содержит MongoDB ObjectId в виде строки (например: `"6364ec62cb6ce6000c3e16ef"`).

### 2. HeroPass содержит название клуба
View `ris.v_user_heropass` уже содержит поле `heropass_club_name` - не нужен дополнительный запрос!

### 3. InBody поля
- `pbf` - процент жира в теле (body fat percentage)
- `smm` - скелетная мышечная масса (skeletal muscle mass)
- `fs` - фитнес балл (fitness score)
- `wt` - вес (weight)

### 4. Checkins содержат program_type
View показывает `programset_type` для каждого посещения - отлично для анализа истории!

### 5. Marathons в PostgreSQL
Марафоны доступны через view `ris.v_user_marathons` с полной информацией о посещаемости.

---

## 📋 Использование

### Базовый пример

```python
from utils.data_loader import UserDataLoader

# MongoDB ObjectId пользователя в виде строки
user_id = "6364ec62cb6ce6000c3e16ef"

# Загрузить все данные
user_data = UserDataLoader.load_all_data(user_id)

print(f"Профиль: {user_data['user_profile']}")
print(f"InBody: {user_data['inbody_data']}")
print(f"Посещений: {len(user_data['checkins_data'])}")
print(f"Марафонов: {len(user_data['marathons_data'])}")
print(f"HeroPass: {user_data['heropass_data']}")
```

### Тестирование конкретного пользователя

```bash
# Протестировать загрузку данных
python test_data_loader.py 6364ec62cb6ce6000c3e16ef

# Результат сохраняется в user_data_<user_id>.json
```

### Генерация плана с реальными данными

```python
from generators.plan_generator import RecommendedPlanGenerator
from utils.data_loader import UserDataLoader

user_id = "6364ec62cb6ce6000c3e16ef"

# 1. Загрузить данные
user_data = UserDataLoader.load_all_data(user_id)

# 2. Проверить анкету
if not user_data['questionnaire']:
    print("⚠️ Анкета не найдена - используйте тестовые данные")
    # На этапе разработки используем файл с анкетой
    questionnaire = load_questionnaire_from_file()
else:
    questionnaire = user_data['questionnaire']

# 3. Генерация
generator = RecommendedPlanGenerator()
result = generator.generate(
    user_id=user_id,
    questionnaire_data=questionnaire,
    inbody_data=user_data['inbody_data'],
    checkins_data=user_data['checkins_data'],
    marathons_data=user_data['marathons_data'],
    heropass_data=user_data['heropass_data']
)

print(f"✓ План сгенерирован: {len(result['recommendedPlan'])} тренировок")
```

---

## 🔧 Настройка .env

```env
# PostgreSQL
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# MongoDB
MONGO_CONNECTION_STRING=mongodb://your_host:27017
MONGO_DB=hero-app-prod

# Gemini API
GEMINI_API_KEY=your_api_key
```

---

## ✅ Чек-лист

- [x] Обновлены все запросы в `postgres_connection.py`
- [x] Обновлён `data_loader.py` для правильного маппинга
- [x] Создан `check_db_structure.py` для проверки структуры
- [x] Создан `test_data_loader.py` для тестирования
- [x] Все поля правильно маппятся
- [x] HeroPass берётся из PostgreSQL (с fallback на MongoDB)
- [x] Marathons берутся из PostgreSQL
- [x] Checkins содержат program_type для анализа
- [x] InBody поля корректно конвертируются

---

## 🚀 Следующие шаги

1. **Протестировать с реальным user_id**:
   ```bash
   python test_data_loader.py <real_user_id>
   ```

2. **Проверить результаты** в файле `user_data_<user_id>.json`

3. **Запустить генерацию плана**:
   ```bash
   python example_usage_with_db.py <real_user_id>
   ```

4. **Если анкета не найдена** - добавить тестовую анкету в файл или создать в MongoDB

---

## 📝 Примечания

- **Анкета на этапе разработки**: Если `userblocks.forms` пуст, система вернёт `None`. Нужно либо создать тестовый блок с формой, либо использовать файл с анкетой.

- **ObjectId как строка**: Все `user_id` в PostgreSQL - это строки с MongoDB ObjectId. Не нужна конвертация.

- **HeroPass fallback**: Если HeroPass не найден в PostgreSQL, система автоматически проверит MongoDB.

- **Обработка ошибок**: Все методы имеют try-catch и возвращают безопасные значения (None, []) при ошибках.
