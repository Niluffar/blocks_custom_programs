"""
Универсальная генерация плана для любого пользователя
Использование:
    python generate_plan.py <телефон_или_имя> <user_id>

Примеры:
    python generate_plan.py 87000701471 6655876bdc61e0003259b459
    python generate_plan.py "Адиль" 6655876bdc61e0003259b459
    python generate_plan.py 87001234567 665587abc123def456789012
"""
from generators.plan_generator import RecommendedPlanGenerator
from utils.data_loader import UserDataLoader
from utils.questionnaire_loader import load_questionnaire_for_user
from db import MongoConnection, PostgresConnection
import csv
import json
import logging
import os
import sys

# Включаем подробное логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)


DAY_NAMES = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Вс'}


def print_plan_summary(result: dict):
    """
    Читаемая сводка сгенерированного плана:
    - Метаданные (цель, частота, график, клуб)
    - Неделя за неделей: список тренировок
    - Распределение типов в процентах
    - Задачи (tasksProgress)
    """
    meta = result.get('metadata', {})
    plan = result.get('recommendedPlan', [])
    tasks = result.get('tasksProgress', [])

    # --- Метаданные ---
    print("\n" + "=" * 60)
    print("СВОДКА ПЛАНА")
    print("=" * 60)
    print(f"  Цель:           {meta.get('goal', '?')}")
    print(f"  Уровень:        {meta.get('progression_level', '?')}")
    print(f"  Базовая частота: {meta.get('frequency', '?')} тренировок/неделю")
    schedule = meta.get('weekly_schedule', [])
    if schedule:
        schedule_str = '  '.join([f"W{i+1}:{s}" for i, s in enumerate(schedule)])
        print(f"  График:         {schedule_str}")
        print(f"  Всего:          {sum(schedule)} тренировок за 8 недель")
    if meta.get('club_name'):
        print(f"  Клуб:           {meta['club_name']}")
    if meta.get('focus_areas'):
        print(f"  Фокус:          {', '.join(meta['focus_areas'])}")

    # --- Таблица расписания ---
    print("\n" + "-" * 80)
    print("РАСПИСАНИЕ")
    print("-" * 80)

    type_counts = {}
    total_workouts = 0

    # Собираем данные: week_data[week][day] = primary_type
    week_data = {}
    for item in plan:
        w = item.get('week', 0)
        d = item.get('day', 0)
        types = item.get('programSetTypes', [])
        primary = types[0] if types else '?'
        week_data.setdefault(w, {})[d] = primary
        total_workouts += 1
        type_counts[primary] = type_counts.get(primary, 0) + 1

    # Ширина колонок
    col_w = 12
    header = "          " + "".join(f"{DAY_NAMES.get(d, '?'):^{col_w}}" for d in range(1, 8))

    for part in [1, 2]:
        part_weeks = range(1, 5) if part == 1 else range(5, 9)
        print(f"\n  Part {part}")
        print(f"  {header}")
        print(f"  {'':>10}" + "-" * (col_w * 7))

        for week in part_weeks:
            row = f"  W{week:<8}"
            for day in range(1, 8):
                cell = week_data.get(week, {}).get(day, '')
                row += f"{cell:^{col_w}}"
            exp = schedule[week - 1] if schedule and len(schedule) >= week else '?'
            row += f"  | {exp} тр."
            print(row)

        print(f"  {'':>10}" + "-" * (col_w * 7))

    # --- Распределение типов ---
    print("\n" + "-" * 60)
    print("РАСПРЕДЕЛЕНИЕ ТИПОВ")
    print("-" * 60)

    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
    for t, count in sorted_types:
        pct = (count / total_workouts * 100) if total_workouts else 0
        bar = '#' * int(pct / 2)
        print(f"  {t:<22} {count:>2} ({pct:4.1f}%)  {bar}")

    print(f"\n  Итого: {total_workouts} тренировок")

    # --- Задачи ---
    if tasks:
        print("\n" + "-" * 60)
        print("ЗАДАЧИ (tasksProgress)")
        print("-" * 60)
        for i, task in enumerate(tasks, 1):
            types_str = ', '.join(task.get('programSetTypes', []))
            print(f"  {i}. [{task.get('part', '?')}] {task.get('text', '?')} (target: {task.get('target', '?')}) [{types_str}]")

    print()


def save_plan_csv(result: dict, csv_path: str):
    """
    Сохранить план в CSV для вставки в Google Sheets.
    Содержит метаданные, таблицу расписания (Part 1 + Part 2) и распределение типов.
    """
    meta = result.get('metadata', {})
    plan = result.get('recommendedPlan', [])
    schedule = meta.get('weekly_schedule', [])

    # Собираем week_data[week][day] = primary_type
    week_data = {}
    type_counts = {}
    total_workouts = 0
    for item in plan:
        w = item.get('week', 0)
        d = item.get('day', 0)
        types = item.get('programSetTypes', [])
        primary = types[0] if types else '?'
        week_data.setdefault(w, {})[d] = primary
        total_workouts += 1
        type_counts[primary] = type_counts.get(primary, 0) + 1

    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # Метаданные
        writer.writerow(['Цель', meta.get('goal', '')])
        writer.writerow(['Уровень', meta.get('progression_level', '')])
        writer.writerow(['Частота', f"{meta.get('frequency', '')} тр/нед"])
        writer.writerow(['Клуб', meta.get('club_name', '')])
        if meta.get('focus_areas'):
            writer.writerow(['Фокус', ', '.join(meta['focus_areas'])])
        if schedule:
            writer.writerow(['График', ' | '.join(f"W{i+1}:{s}" for i, s in enumerate(schedule))])
            writer.writerow(['Всего', f"{sum(schedule)} тренировок"])
        writer.writerow([])

        # Part 1 и Part 2
        for part in [1, 2]:
            part_weeks = range(1, 5) if part == 1 else range(5, 9)
            writer.writerow([f'Part {part}', *days, 'Тренировок'])
            for week in part_weeks:
                row = [f'W{week}']
                for day in range(1, 8):
                    row.append(week_data.get(week, {}).get(day, ''))
                exp = schedule[week - 1] if schedule and len(schedule) >= week else ''
                row.append(exp)
                writer.writerow(row)
            writer.writerow([])

        # Распределение типов
        writer.writerow(['Тип', 'Кол-во', '%'])
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = (count / total_workouts * 100) if total_workouts else 0
            writer.writerow([t, count, f'{pct:.1f}%'])
        writer.writerow(['Итого', total_workouts, '100%'])


def generate_plan(phone_or_name: str, user_id: str):
    """
    Универсальная генерация плана

    Args:
        phone_or_name: Номер телефона или имя для поиска в CSV
        user_id: MongoDB user_id (ObjectId)
    """
    print("=" * 80)
    print(f"ГЕНЕРАЦИЯ ПЛАНА ТРЕНИРОВОК")
    print(f"Поиск в CSV: {phone_or_name}")
    print(f"User ID: {user_id}")
    print("=" * 80)

    try:
        # 1. Загрузка анкеты из CSV
        print("\n[1/6] Загрузка анкеты из CSV файла...")
        questionnaire = load_questionnaire_for_user(phone_or_name=phone_or_name)

        if not questionnaire:
            print(f"  [ERROR] ОШИБКА: Анкета не найдена для '{phone_or_name}'!")
            print("  Проверьте:")
            print("    - CSV файл: 'data/Анкета для составления программы тренировок  (Responses) - Form Responses 1.csv'")
            print(f"    - Имя или телефон '{phone_or_name}' есть в файле")
            return

        print(f"  [OK] Анкета загружена: {questionnaire.get('name')}")
        print(f"    Телефон: {questionnaire.get('phone')}")
        print(f"    Цель: {questionnaire.get('goal')}")
        print(f"    Опыт: {questionnaire.get('experience')}")

        # 2. Загрузка остальных данных из баз
        print("\n[2/6] Загрузка данных из PostgreSQL и MongoDB...")
        user_data = UserDataLoader.load_all_data(user_id)

        print(f"  [OK] Профиль: {'найден' if user_data['user_profile'] else 'не найден'}")
        print(f"  [OK] InBody: {'найден' if user_data['inbody_data'] else 'не найден'}")
        print(f"  [OK] Посещения: {len(user_data['checkins_data'])} записей")
        print(f"  [OK] Марафоны: {len(user_data['marathons_data'])} записей")
        print(f"  [OK] HeroPass: {'активен' if user_data['heropass_data'] else 'не найден'}")

        # 3. Отображение профиля
        print("\n[3/6] Анализ профиля пользователя...")
        print(f"  Цель: {questionnaire.get('goal')}")
        print(f"  Опыт: {questionnaire.get('experience')}")
        print(f"  Фокус: {', '.join(questionnaire.get('focus', []))}")
        print(f"  Возраст: {questionnaire.get('age')} лет, рост {questionnaire.get('height')} см, вес {questionnaire.get('weight')} кг")
        print(f"  Текущая форма: {questionnaire.get('current_form')}")
        print(f"  Ограничения: {questionnaire.get('health_restrictions') or 'нет'}")

        if user_data['heropass_data']:
            print(f"  Клуб: {user_data['heropass_data'].get('club_name')}")

        # Статистика посещений
        if user_data['checkins_data']:
            avg_per_week = (len(user_data['checkins_data']) / 90) * 7
            print(f"  Средняя частота посещений: {avg_per_week:.1f} раз/неделю")

        # 4. Инициализация генератора
        print("\n[4/6] Инициализация генератора...")
        generator = RecommendedPlanGenerator()

        # 5. Генерация плана
        print("\n[5/6] Генерация плана через LLM (Gemini API)...")
        print("  (это может занять 30-60 секунд)")

        result = generator.generate(
            user_id=user_id,
            questionnaire_data=questionnaire,  # ← Анкета из CSV
            inbody_data=user_data['inbody_data'],
            checkins_data=user_data['checkins_data'],
            marathons_data=user_data['marathons_data'],
            heropass_data=user_data['heropass_data'],
            max_attempts=3
        )

        # 6. Вывод результатов
        print("\n[OK] План успешно сгенерирован!")
        print_plan_summary(result)

        # 7. Сохранение в файл
        print("\n[6/6] Сохранение результатов...")

        # Формируем имя файла из user_id
        safe_name = questionnaire.get('name', user_id).lower().replace(' ', '_')
        output_file = os.path.join('output', f'plan_{safe_name}_{user_id[:8]}.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Полный план сохранён в: {output_file}")

        csv_file = output_file.replace('.json', '_schedule.csv')
        save_plan_csv(result, csv_file)
        print(f"  [OK] CSV для Google Sheets: {csv_file}")

        print("\n" + "=" * 80)
        print("[OK] УСПЕШНО! План готов к использованию")
        print("=" * 80)

        print("\nСледующие шаги:")
        print(f"1. Просмотрите полный план в файле: {output_file}")
        print("2. Для сохранения в MongoDB создайте userblock и вызовите:")
        print("   from db import MongoConnection")
        print(f"   userblock_id = MongoConnection.create_user_block(user_id='{user_id}')")
        print("   MongoConnection.update_user_block(userblock_id, {")
        print("       'recommendedPlan': result['recommendedPlan'],")
        print("       'tasksProgress': result['tasksProgress']")
        print("   })")

    except Exception as e:
        print(f"\n[ERROR] ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Закрываем соединения
        MongoConnection.close()
        PostgresConnection.close()


def print_usage():
    """Вывести инструкцию по использованию."""
    print("\n" + "=" * 80)
    print("УНИВЕРСАЛЬНАЯ ГЕНЕРАЦИЯ ПЛАНА ТРЕНИРОВОК")
    print("=" * 80)
    print("\nИспользование:")
    print("  python generate_plan.py <телефон_или_имя> <user_id>")
    print("\nАргументы:")
    print("  телефон_или_имя - Номер телефона или имя из CSV файла")
    print("  user_id         - MongoDB ObjectId пользователя")
    print("\nПримеры:")
    print("  # По номеру телефона")
    print("  python generate_plan.py 87000701471 6655876bdc61e0003259b459")
    print("\n  # По имени (в кавычках если содержит пробелы)")
    print('  python generate_plan.py "Адиль Е" 6655876bdc61e0003259b459')
    print("\n  # По части имени")
    print("  python generate_plan.py Адиль 6655876bdc61e0003259b459")
    print("\nТребования:")
    print("  1. CSV файл: 'data/Анкета для составления программы тренировок  (Responses) - Form Responses 1.csv'")
    print("  2. .env файл с переменными:")
    print("     - GEMINI_API_KEY")
    print("     - POSTGRES_CONNECTION_STRING")
    print("     - MONGODB_CONNECTION_STRING")
    print("\nРезультат:")
    print("  Создаётся файл output/plan_<имя>_<user_id>.json с полным планом тренировок")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    # Проверка аргументов
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)

    phone_or_name = sys.argv[1]
    user_id = sys.argv[2]

    # Валидация user_id (должен быть 24 символа для MongoDB ObjectId)
    if len(user_id) != 24:
        print(f"\n[WARNING] User ID выглядит некорректным: {user_id}")
        print("MongoDB ObjectId должен быть 24 символа (например: 6655876bdc61e0003259b459)")
        print("Продолжаем с этим ID, но запросы к MongoDB могут не сработать...\n")

    generate_plan(phone_or_name, user_id)
