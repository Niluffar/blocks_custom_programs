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
import json
import logging
import sys

# Включаем подробное логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)


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
            print("    - CSV файл: 'Анкета для составления программы тренировок  (Responses) - Form Responses 1.csv'")
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
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ ГЕНЕРАЦИИ")
        print("=" * 80)

        # Метаданные
        metadata = result['metadata']
        print(f"\nМЕТАДАННЫЕ:")
        print(f"  Частота: {metadata['frequency']} тренировок/неделю")
        print(f"  Историческая частота: {metadata.get('historical_frequency', 'N/A'):.1f} раз/неделю")
        print(f"  Уровень прогрессии: {metadata['progression_level']}")
        print(f"  Цель: {metadata['goal']}")
        print(f"  Фокус: {', '.join(metadata['focus_areas'])}")
        print(f"  Клуб: {metadata.get('club_name', 'Не указан')}")

        # Статистика плана
        print(f"\nСТАТИСТИКА ПЛАНА:")
        print(f"  Всего тренировок: {metadata['total_workouts']}")
        print(f"  Всего задач: {metadata['total_tasks']}")
        print(f"  Недель: 8 (Part 1: недели 1-4, Part 2: недели 5-8)")

        # Распределение по типам программ
        stats = generator.get_generation_stats(result)
        print(f"\nРАСПРЕДЕЛЕНИЕ ПО ТИПАМ ПРОГРАММ:")
        for ptype, count in sorted(stats['type_distribution'].items(), key=lambda x: -x[1]):
            percentage = (count / stats['total_workouts']) * 100
            print(f"  {ptype}: {count} тренировок ({percentage:.1f}%)")

        # Примеры тренировок
        print(f"\nПРИМЕР ТРЕНИРОВОК (первая неделя):")
        week1 = [w for w in result['recommendedPlan'] if w['week'] == 1]
        for i, workout in enumerate(week1, 1):
            day_names = {1: 'ПН', 2: 'ВТ', 3: 'СР', 4: 'ЧТ', 5: 'ПТ', 6: 'СБ', 7: 'ВС'}
            day_name = day_names.get(workout['day'], workout['day'])
            print(f"\n  {i}. Неделя {workout['week']}, {day_name} (день {workout['day']})")
            print(f"     {workout['text']}")
            print(f"     Основной: {workout['programSetTypes'][0]}")
            if len(workout['programSetTypes']) > 1:
                print(f"     Альтернативы: {', '.join(workout['programSetTypes'][1:])}")

        # Примеры задач
        print(f"\nПРИМЕР ЗАДАЧ (Part 1):")
        part1_tasks = [t for t in result['tasksProgress'] if t['part'] == 1][:5]
        for i, task in enumerate(part1_tasks, 1):
            print(f"\n  {i}. {task['text']}")
            print(f"     Цель: {task['target']}, выполнено: {task['done']}")
            print(f"     Программы: {', '.join(task['programSetTypes'])}")

        # 7. Сохранение в файл
        print("\n[6/6] Сохранение результатов...")

        # Формируем имя файла из user_id
        safe_name = questionnaire.get('name', user_id).lower().replace(' ', '_')
        output_file = f'plan_{safe_name}_{user_id[:8]}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Полный план сохранён в: {output_file}")

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
    print("  1. CSV файл: 'Анкета для составления программы тренировок  (Responses) - Form Responses 1.csv'")
    print("  2. .env файл с переменными:")
    print("     - GEMINI_API_KEY")
    print("     - POSTGRES_CONNECTION_STRING")
    print("     - MONGODB_CONNECTION_STRING")
    print("\nРезультат:")
    print("  Создаётся файл plan_<имя>_<user_id>.json с полным планом тренировок")
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
