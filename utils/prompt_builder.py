"""
Построение промптов для Gemini API
Формирует детальные инструкции для LLM на основе профиля пользователя,
доступных программ, правил восстановления и edge cases
"""
from typing import Dict, List, Any
from models.user_profile import UserProfile
from rules.goal_mappings import GOAL_TO_TYPES


class PromptBuilder:
    """
    Строит промпты для Gemini API с учётом:
    - Профиля пользователя (цель, опыт, ограничения)
    - Доступных типов программ в клубе
    - Правил восстановления мышц
    - Edge cases (ограничения здоровья, перерывы и т.д.)
    - Примеров паттернов из контекстных файлов
    """

    def build_prompt(
        self,
        user_profile: UserProfile,
        available_types: List[str],
        recovery_rules: Dict[str, Dict],
        pattern_examples: List[Dict[str, Any]],
        reshape_per_block: int = 0
    ) -> str:
        """
        Построить полный промпт для Gemini API.

        Args:
            user_profile: Профиль пользователя
            available_types: Доступные типы программ в клубе
            recovery_rules: Правила восстановления мышц
            pattern_examples: Примеры паттернов из контекстных файлов
            reshape_per_block: Лимит Reshape тренировок на этот блок (0 = недоступен)

        Returns:
            str: Полный промпт для LLM
        """
        # Базовая структура промпта
        prompt = f"""Ты фитнес-эксперт Hero Fitness. Создай ИНДИВИДУАЛЬНЫЙ план тренировок на 8 недель.

ПРОФИЛЬ АТЛЕТА:
- Цель: {self._format_goal(user_profile.goal)}
- Фокусные области: {', '.join(user_profile.focus_areas)}
- Опыт: {user_profile.experience_level} (Уровень прогрессии: {user_profile.progression_level})
- Частота: {user_profile.frequency} тренировок в неделю
- Пол: {user_profile.gender}, Возраст: {user_profile.age} лет
- Текущая форма: {user_profile.body_type}
- Ограничения по здоровью: {user_profile.health_restrictions if user_profile.health_restrictions else 'нет'}

ДОСТУПНЫЕ ПРОГРАММЫ В КЛУБЕ:
{', '.join(available_types)}

РЕКОМЕНДОВАННОЕ РАСПРЕДЕЛЕНИЕ ДЛЯ ЦЕЛИ "{self._format_goal(user_profile.goal)}":
{self._format_recommended_distribution(user_profile.goal, available_types)}

ВАЖНО - ПРИОРИТЕТЫ ПРИ СОСТАВЛЕНИИ ПЛАНА:
1. Основная цель атлета ({self._format_goal(user_profile.goal)}) - это 60-70% приоритета
   → Следуй рекомендованному распределению программ для этой цели
   → Используй типы программ которые максимально эффективны для достижения цели

2. Фокусные области ({', '.join(user_profile.focus_areas)}) - это 30-40% приоритета
   → Добавляй программы для фокусных областей, НО не в ущерб основной цели
   → Например: цель "похудение" + фокус "ноги" = много Bootcamp/Metcon + Legs, а НЕ только Legs

3. Баланс = цель доминирует, фокус дополняет
   → Если цель "похудение" → минимум 50-60% тренировок должны быть кардио/метаболические
   → Если цель "масса" → минимум 60-70% тренировок должны быть силовые сплиты
   → Фокусные области учитываются ВНУТРИ этого распределения

ВАРИАТИВНОСТЬ И РАЗНООБРАЗИЕ:
1. Используй МИНИМУМ 5-6 разных типов программ за 8 недель
   → Не ограничивайся только самыми популярными типами
   → Разнообразие = больше мотивации и лучшие результаты

2. Избегай полностью одинаковых недель
   → Максимум 2 недели подряд с одинаковым паттерном
   → Каждые 2-3 недели вноси изменения в структуру

3. Прогрессия через разнообразие в Part 2 (недели 5-8):
   → Введи 1-2 НОВЫХ типа программ которых не было в Part 1
   → Увеличь сложность через вариативность, не только через частоту

4. Учитывай фокусные области через РАЗНЫЕ программы:
{self._format_focus_variety_instructions(user_profile.focus_areas, available_types)}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:

1. Соблюдай восстановление мышц между тренировками:
{self._format_recovery_rules(recovery_rules)}

2. Используй ТОЛЬКО доступные типы программ из списка выше.
   ИСКЛЮЧЕНИЯ: НЕ используй education, assessment и endGame - это специальные программы (онбординг и финальные испытания), не для регулярных тренировочных планов.

3. Прогрессия нагрузки:
   - Недели 1-4 (part=1): базовый уровень интенсивности
   - Недели 5-8 (part=2): повышенная интенсивность

4. Распределение тренировок по дням недели:
   - 3 тренировки: Понедельник (день 1), Среда (день 3), Пятница (день 5)
   - 4 тренировки: Понедельник (день 1), Вторник (день 2), Четверг (день 4), Пятница (день 5)
   - 5 тренировок: Понедельник (день 1), Вторник (день 2), Среда (день 3), Пятница (день 5), Суббота (день 6)

5. Для каждого дня добавь 1-2 альтернативных типа программ в массив programSetTypes.
   - Первый элемент - основной тип программы
   - Следующие 1-2 элемента - альтернативы на случай занятости зала

{self._format_reshape_limit(reshape_per_block)}
{self._add_edge_case_instructions(user_profile)}

ПРИМЕРЫ ПАТТЕРНОВ (для понимания логики, НЕ КОПИРУЙ 1:1):
{self._format_pattern_examples(pattern_examples)}

ВАЖНО: Создай УНИКАЛЬНЫЙ план специально для этого атлета, учитывая:
- Его основную цель ({self._format_goal(user_profile.goal)})
- Фокусные области ({', '.join(user_profile.focus_areas)})
- Уровень опыта и прогрессии
- Текущую форму и возраст

Примеры выше показывают только общие принципы построения программ.
НЕ копируй их напрямую - создавай индивидуальный план под этого конкретного человека.

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО JSON массив без дополнительного текста, в следующем формате:
[
  {{
    "text": "Выполни тренировку BootCamp",
    "week": 1,
    "day": 1,
    "programSetTypes": ["bootcamp", "metcon"],
    "part": 1
  }},
  ...
]

ВАЖНО - ФОРМАТ ПОЛЯ "text":
Поле "text" должно быть КОРОТКИМ и СТАНДАРТНЫМ, строго по шаблону:
  "Выполни тренировку <Название программы>"
Примеры:
  - "Выполни тренировку BootCamp"
  - "Выполни тренировку Legs"
  - "Выполни тренировку Upper Body"
  - "Выполни тренировку Push"
  - "Выполни тренировку Pull"
  - "Выполни тренировку Full Body"
  - "Выполни тренировку Functional Full Body"
  - "Выполни тренировку MetCon"
  - "Выполни тренировку Glute Lab"
  - "Выполни тренировку Arms"
  - "Выполни тренировку Mind & Body"
  - "Выполни тренировку Reshape"
НЕ добавляй мотивационные фразы, советы или описания в поле text.
Только "Выполни тренировку <Название>".
"""
        return prompt

    def _format_goal(self, goal: str) -> str:
        """Форматировать цель для промпта."""
        goal_descriptions = {
            'похудение': 'Снижение веса и жиросжигание',
            'масса': 'Набор мышечной массы',
            'рельеф': 'Тонус и рельеф',
            'здоровье': 'Улучшение здоровья и выносливости',
            'поддержание': 'Поддержание текущей формы'
        }
        return goal_descriptions.get(goal, goal)

    def _format_recovery_rules(self, recovery_rules: Dict[str, Dict]) -> str:
        """Форматировать правила восстановления для промпта."""
        rules_text = []

        for program_type, rules in recovery_rules.items():
            conflicts = ', '.join(rules.get('conflicts', []))
            recovery_days = rules.get('recovery_days', 1)

            rules_text.append(
                f"   - {program_type.upper()}: нужно {recovery_days} дня восстановления. "
                f"Не ставь {program_type} если в предыдущие {recovery_days} дня были: {conflicts}"
            )

        return '\n'.join(rules_text)

    def _format_recommended_distribution(self, goal: str, available_types: List[str]) -> str:
        """
        Форматировать рекомендованное распределение программ для цели.
        Показывает процентное соотношение типов программ из goal_mappings.
        """
        if goal not in GOAL_TO_TYPES:
            return "(Распределение для этой цели не определено)"

        goal_weights = GOAL_TO_TYPES[goal]

        # Фильтруем только доступные типы
        available_weights = {
            ptype: weight
            for ptype, weight in goal_weights.items()
            if ptype in available_types
        }

        if not available_weights:
            return "(Нет доступных программ для этой цели в клубе)"

        # Перенормализация весов если некоторые типы недоступны
        total = sum(available_weights.values())
        normalized = {k: v/total for k, v in available_weights.items()}

        # Форматирование в проценты
        distribution_lines = []
        for ptype, weight in sorted(normalized.items(), key=lambda x: -x[1]):
            percentage = int(weight * 100)
            distribution_lines.append(f"   - {ptype}: ~{percentage}% тренировок")

        return '\n'.join(distribution_lines)

    def _format_focus_variety_instructions(
        self,
        focus_areas: List[str],
        available_types: List[str]
    ) -> str:
        """
        Форматировать инструкции по разнообразию для фокусных областей.
        Подсказывает LLM какие типы программ использовать для каждого фокуса.
        """
        if not focus_areas:
            return "   → (Фокусные области не указаны)"

        instructions = []

        # Маппинг фокусов к рекомендуемым типам программ
        focus_to_programs = {
            'верх_тела': ['upperBody', 'push', 'pull', 'armBlast'],
            'ноги': ['legs', 'gluteLab'],
            'выносливость': ['bootcamp', 'metcon', 'functionalFullBody'],
            'баланс': ['mindAndBody', 'reshape', 'fullBody'],
            'спина': ['pull', 'upperBody'],
            'руки': ['armBlast', 'push', 'pull'],
            'ягодицы': ['gluteLab', 'legs'],
            'пресс': ['bootcamp', 'metcon', 'functionalFullBody']
        }

        for focus in focus_areas:
            recommended = focus_to_programs.get(focus, [])
            # Фильтруем только доступные программы
            available_recommended = [p for p in recommended if p in available_types]

            if available_recommended:
                programs_str = ', '.join(available_recommended)
                instructions.append(
                    f"   → Фокус '{focus}': используй {programs_str}"
                )
            else:
                instructions.append(
                    f"   → Фокус '{focus}': нет специфичных программ в клубе, "
                    f"используй базовые (functionalFullBody, fullBody)"
                )

        return '\n'.join(instructions) if instructions else "   → (Рекомендации не найдены)"

    def _format_reshape_limit(self, reshape_per_block: int = 0) -> str:
        """
        Форматировать ограничение на Reshape тренировки.
        reshape_per_block рассчитан из pilatesVisits (лимит на весь абонемент)
        поделённый на количество блоков в абонементе.
        0 = reshape недоступен (нет pilatesVisits в HeroPass).
        """
        if reshape_per_block <= 0:
            return ''  # reshape уже убран из available_types, не нужно дублировать

        return f"""
ОГРАНИЧЕНИЕ ПО RESHAPE: У атлета лимит {reshape_per_block} тренировок Reshape (пилатес на реформерах) на этот блок.
- Максимум {reshape_per_block} тренировок с основным типом "reshape" за 8 недель
- Распредели их равномерно по неделям, не ставь все Reshape подряд
- Не превышай этот лимит — это ограничение абонемента"""

    def _add_edge_case_instructions(self, user_profile: UserProfile) -> str:
        """
        Добавить специальные инструкции для edge cases.

        Включает:
        - Ограничения по здоровью
        - Длительные перерывы
        - Новички
        - Пожилой возраст
        """
        instructions = []

        # Ограничения здоровья - передаём raw text
        # LLM сам поймёт что делать с любым текстом
        if user_profile.health_restrictions:
            instructions.append(f"""
ВАЖНО: У атлета есть ограничения по здоровью: "{user_profile.health_restrictions}"
- Учти эти ограничения при составлении плана
- Исключи или минимизируй упражнения/программы которые могут усугубить проблему
- Подбери безопасные альтернативы с учётом этих ограничений
""")

        # Длительный перерыв
        if user_profile.current_break > 90:
            instructions.append(f"""
ВАЖНО: Атлет не тренировался {user_profile.current_break} дней (более 3 месяцев):
- Первые 2 недели (1-2): адаптация с программами Functional Full Body и Full Body
- Избегай сложных сплитов (Push/Pull) в первый месяц
- Постепенное увеличение нагрузки от недели к неделе
- Недели 5-8 можно увеличить интенсивность
""")

        # Новички после перерыва
        if user_profile.experience_level == 'новичок' and user_profile.current_break > 60:
            instructions.append("""
ВАЖНО: Начинающий атлет после перерыва:
- Первые 2-3 недели: только Functional Full Body, Full Body и Bootcamp
- Постепенное введение специализированных программ (Upper, Legs, Push/Pull) с недели 4
- Избегай сложных силовых сплитов в первый месяц
- Фокус на технике и адаптации к нагрузкам
""")

        # Пожилой возраст (50+)
        if user_profile.age >= 50:
            instructions.append("""
ВАЖНО: Атлет в возрасте 50+:
- Фокус на Mind&Body для гибкости и баланса
- Силовые программы для сохранения мышечной массы (Upper, Legs, Full Body)
- Умеренное кардио (Bootcamp, Metcon)
- Избегай чрезмерно интенсивных программ
""")

        # Полная форма + похудение
        if user_profile.body_type == 'полное' and user_profile.goal == 'похудение':
            instructions.append("""
ВАЖНО: Цель - снижение веса при полной форме:
- Приоритет: Bootcamp и Metcon (высокий расход калорий)
- Дополнительно: Functional Full Body для поддержки мышц
- Меньше акцента на чистые силовые (Push/Pull)
- Постепенное увеличение частоты кардио
""")

        # Спортивная форма + масса
        if user_profile.body_type == 'спортивное' and user_profile.goal == 'масса':
            instructions.append("""
ВАЖНО: Набор массы при спортивной форме:
- Приоритет: Push, Pull, Legs (силовой сплит)
- Минимум кардио (1 раз в неделю Bootcamp или Metcon для здоровья сердца)
- Фокус на прогрессии весов и объёма
- Upper и Full Body для дополнительного объёма
""")

        if instructions:
            return '\n' + '\n'.join(instructions)
        return ''

    def _format_pattern_examples(self, pattern_examples: List[Dict[str, Any]]) -> str:
        """
        Форматировать примеры паттернов из контекстных файлов.

        Args:
            pattern_examples: Список примеров паттернов

        Returns:
            Отформатированная строка с примерами
        """
        if not pattern_examples:
            return '(Примеры не загружены)'

        formatted_examples = []

        for example in pattern_examples:
            path_name = example.get('path', 'Unknown')
            weeks = example.get('weeks', 4)
            frequency = example.get('frequency', '3-4')
            description = example.get('description', '')
            pattern = example.get('pattern', '')

            formatted_examples.append(
                f"- {path_name} ({weeks} недель, {frequency} тренировок/неделю):\n"
                f"  Описание: {description}\n"
                f"  Паттерн: {pattern}"
            )

        return '\n'.join(formatted_examples)

    def build_retry_prompt(
        self,
        original_prompt: str,
        validation_errors: List[str]
    ) -> str:
        """
        Построить промпт для повторной попытки после ошибок валидации.

        Args:
            original_prompt: Оригинальный промпт
            validation_errors: Список ошибок валидации

        Returns:
            Модифицированный промпт с указанием ошибок
        """
        errors_text = '\n'.join([f"- {error}" for error in validation_errors])

        retry_prompt = f"""{original_prompt}

ОШИБКИ В ПРЕДЫДУЩЕЙ ПОПЫТКЕ:
{errors_text}

ИСПРАВЬ ЭТИ ОШИБКИ:
1. Проверь что все программы доступны в клубе
2. Убедись что соблюдены правила восстановления
3. Проверь частоту тренировок для каждой недели
4. Проверь корректность распределения по частям (part 1 и part 2)
5. Убедись что формат JSON правильный

Верни исправленный JSON массив:
"""
        return retry_prompt
