"""
Правила восстановления мышечных групп

Критично для безопасности и эффективности тренировок.
Предотвращает overtraining и обеспечивает адекватное восстановление.
"""
from typing import List, Dict


# Правила восстановления для каждого типа программы
#
# recovery_days = количество ТРЕНИРОВОК (не дней!) между конфликтующими типами
#   recovery_days=1 → нельзя подряд, но можно через одну тренировку
#   recovery_days=0 → без ограничений
#
# ВАЖНО: конфликты СИММЕТРИЧНЫ - если A конфликтует с B, то B конфликтует с A
#
# Группы конфликтов:
#   1. Силовые сплиты (push/pull/upperBody/armBlast) - нельзя подряд, те же мышцы
#   2. Ноги (legs/gluteLab) - нельзя подряд, те же мышцы
#   3. Всё тело (fullBody/functionalFullBody) - нельзя подряд, всё тело + нельзя подряд с upperBody
#   4. Кардио (bootcamp/metcon) - только сами с собой, можно чередовать
#   5. Reshape - только сам с собой (пилатес на реформерах)
#
RECOVERY_RULES: Dict[str, Dict] = {
    'push': {
        'conflicts': ['push', 'upperBody', 'armBlast'],
        'recovery_days': 1,
        'muscle_groups': ['chest', 'shoulders', 'triceps'],
        'description': 'Жимовые движения - грудь, плечи, трицепс'
    },
    'pull': {
        'conflicts': ['pull', 'upperBody', 'armBlast'],  # armBlast добавлен (бицепс пересекается)
        'recovery_days': 1,
        'muscle_groups': ['back', 'biceps'],
        'description': 'Тяговые движения - спина, бицепс'
    },
    'legs': {
        'conflicts': ['legs', 'gluteLab', 'bootcamp'],  # bootcamp нагружает ноги после legs = перегрузка
        'recovery_days': 1,
        'muscle_groups': ['quads', 'hamstrings', 'glutes'],
        'description': 'Ноги - квадрицепсы, задняя поверхность бедра, ягодицы'
    },
    'upperBody': {
        'conflicts': ['push', 'pull', 'upperBody', 'armBlast', 'fullBody', 'functionalFullBody'],
        'recovery_days': 1,
        'muscle_groups': ['chest', 'back', 'shoulders', 'arms'],
        'description': 'Весь верх тела - комплексная нагрузка'
    },
    'bootcamp': {
        'conflicts': ['bootcamp'],  # Можно чередовать с metcon
        'recovery_days': 1,
        'muscle_groups': ['full_body', 'cardiovascular'],
        'description': 'Высокоинтенсивные кардио + силовые'
    },
    'metcon': {
        'conflicts': ['metcon'],  # Можно чередовать с bootcamp
        'recovery_days': 1,
        'muscle_groups': ['full_body', 'cardiovascular'],
        'description': 'Metabolic conditioning - кардио выносливость'
    },
    'fullBody': {
        'conflicts': ['fullBody', 'functionalFullBody', 'upperBody'],
        'recovery_days': 1,
        'muscle_groups': ['full_body'],
        'description': 'Все тело - комплексная силовая тренировка'
    },
    'functionalFullBody': {
        'conflicts': ['functionalFullBody', 'fullBody', 'upperBody'],
        'recovery_days': 1,
        'muscle_groups': ['full_body', 'core'],
        'description': 'Функциональная тренировка всего тела'
    },
    'reshape': {
        'conflicts': ['reshape'],  # Только сам с собой, пилатес не конфликтует с силовыми
        'recovery_days': 1,
        'muscle_groups': ['core', 'stabilizers', 'flexibility'],
        'description': 'Reshape - функциональный пилатес на реформерах'
    },
    'gluteLab': {
        'conflicts': ['gluteLab', 'legs'],
        'recovery_days': 1,
        'muscle_groups': ['glutes', 'hamstrings'],
        'description': 'Фокус на ягодицы'
    },
    'armBlast': {
        'conflicts': ['armBlast', 'push', 'pull', 'upperBody'],
        'recovery_days': 1,
        'muscle_groups': ['biceps', 'triceps', 'forearms'],
        'description': 'Фокус на руки'
    },
    'mindAndBody': {
        'conflicts': [],  # Йога и растяжка не конфликтуют
        'recovery_days': 0,
        'muscle_groups': ['flexibility', 'mobility'],
        'description': 'Йога, растяжка, мобильность'
    },
    'assessment': {
        'conflicts': ['assessment'],
        'recovery_days': 3,  # Assessment интенсивный, нужно восстановление
        'muscle_groups': ['full_body'],
        'description': 'Оценка физической подготовки'
    },
    'education': {
        'conflicts': [],  # Теория не требует восстановления
        'recovery_days': 0,
        'muscle_groups': [],
        'description': 'Теоретическое занятие'
    },
    'endGame': {
        'conflicts': ['endGame', 'fullBody'],
        'recovery_days': 2,
        'muscle_groups': ['full_body'],
        'description': 'Продвинутая функциональная тренировка'
    },
}


def can_perform(program_type: str, recent_workouts: List[str]) -> bool:
    """
    Проверяет возможность выполнения программы на основе недавних тренировок.

    Args:
        program_type: Тип программы для проверки
        recent_workouts: Список предыдущих тренировок В ХРОНОЛОГИЧЕСКОМ ПОРЯДКЕ
                        (от старых к новым, т.е. [Monday, Wednesday] если проверяем Friday)

    Returns:
        True если программу можно выполнить (правила восстановления соблюдены)
    """
    if program_type not in RECOVERY_RULES:
        # Если правил нет, считаем что можно выполнять
        return True

    rules = RECOVERY_RULES[program_type]
    recovery_days = rules['recovery_days']
    conflicts = rules['conflicts']

    # Проверяем предыдущие тренировки
    # recovery_days означает "сколько ДРУГИХ тренировок должно быть между повторами"
    # Пример: recent_workouts=[Mon:bootcamp, Wed:legs], checking Fri:bootcamp
    # recovery_days=1 → нужна минимум 1 другая тренировка между bootcamp'ами
    # Между Mon и Fri есть Wed (1 тренировка) → OK

    for i, past_type in enumerate(recent_workouts):
        # Считаем сколько тренировок между past_type и текущей
        # recent_workouts = [0:Monday, 1:Wednesday], мы проверяем Friday
        # Если i=0 (Monday), то между Monday и Friday: len([Wednesday]) = 1 тренировка
        # Если i=1 (Wednesday), то между Wednesday и Friday: len([]) = 0 тренировок
        workouts_between = len(recent_workouts) - 1 - i

        # Если конфликтующая программа была и между ними недостаточно тренировок
        if past_type in conflicts and workouts_between < recovery_days:
            return False

    return True


def get_available_types(all_types: List[str], recent_workouts: List[str]) -> List[str]:
    """
    Возвращает список доступных типов программ на основе правил восстановления.

    Args:
        all_types: Все возможные типы программ
        recent_workouts: Список последних тренировок

    Returns:
        Список типов программ которые можно выполнить
    """
    available = []
    for program_type in all_types:
        if can_perform(program_type, recent_workouts):
            available.append(program_type)
    return available


def get_recovery_info(program_type: str) -> Dict:
    """
    Получить информацию о правилах восстановления для типа программы.

    Args:
        program_type: Тип программы

    Returns:
        Словарь с информацией о восстановлении
    """
    return RECOVERY_RULES.get(program_type, {
        'conflicts': [],
        'recovery_days': 0,
        'muscle_groups': [],
        'description': 'Неизвестный тип программы'
    })


def get_muscle_groups(program_type: str) -> List[str]:
    """
    Получить список мышечных групп задействованных в программе.

    Args:
        program_type: Тип программы

    Returns:
        Список мышечных групп
    """
    rules = RECOVERY_RULES.get(program_type, {})
    return rules.get('muscle_groups', [])
