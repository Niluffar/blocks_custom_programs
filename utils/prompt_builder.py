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
        reshape_per_block: int = 0,
        weekly_schedule: List[int] = None
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
        # Понедельный график частот
        schedule = weekly_schedule or user_profile.weekly_schedule
        total_workouts = sum(schedule)
        schedule_str = ', '.join([f"W{i+1}:{s}" for i, s in enumerate(schedule)])

        # Базовая структура промпта
        prompt = f"""Ты фитнес-эксперт Hero Fitness. Создай ИНДИВИДУАЛЬНЫЙ план тренировок на 8 недель.

ПРОФИЛЬ АТЛЕТА:
- Цель: {self._format_goal(user_profile.goal)}
- Фокусные области: {', '.join(user_profile.focus_areas)}
- Опыт: {user_profile.experience_level} (Уровень прогрессии: {user_profile.progression_level})
- Базовая частота: {user_profile.frequency} тренировок в неделю
- Пол: {user_profile.gender}, Возраст: {user_profile.age} лет
- Текущая форма: {user_profile.body_type}
- Ограничения по здоровью: {user_profile.health_restrictions if user_profile.health_restrictions else 'нет'}

ВОЛНООБРАЗНАЯ ПЕРИОДИЗАЦИЯ (ОБЯЗАТЕЛЬНО):
Частота тренировок МЕНЯЕТСЯ от недели к неделе для оптимального восстановления и прогресса.
График: {schedule_str}
Общее количество тренировок за 8 недель: {total_workouts}
- Недели с пониженной частотой (deload) — это разгрузочные недели для восстановления
- СТРОГО соблюдай указанное количество тренировок для КАЖДОЙ недели

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
   → ЗАПРЕЩЕНО: один тип программ более 25% от общего числа тренировок
   → Если два типа по сути похожи (bootcamp и metcon — оба кардио), их СУММА:
     • Для цели "похудение": не должна превышать 55% (допустимо больше кардио)
     • Для других целей: не должна превышать 45%

2. ОБЯЗАТЕЛЬНЫЙ БАЛАНС силовых и кардио (для ЛЮБОЙ цели):
   → Минимум 20% тренировок = силовые (push, pull, legs, upperBody, armBlast, gluteLab, fullBody, functionalFullBody)
   → Минимум 15% тренировок = кардио/метаболические (bootcamp, metcon)
   → Даже при цели "похудение" НЕЛЬЗЯ делать 100% кардио — силовые сохраняют мышцы
   → Даже при цели "масса" НЕЛЬЗЯ делать 100% силовые — кардио поддерживает здоровье сердца

3. Избегай полностью одинаковых недель
   → ЗАПРЕЩЕНО: две полностью идентичные недели (одинаковые типы в одинаковом порядке)
   → Каждые 2 недели вноси заметные изменения в структуру
   → Меняй порядок тренировок, вводи новые типы, чередуй акценты

4. На неделях с 5+ тренировками — добавляй разнообразие (рекомендация):
   → При 5 и более тренировках в неделю желательно включить хотя бы 1 "акцентную" или кардио тренировку
     (armBlast, bootcamp, metcon, gluteLab) вдобавок к основным силовым сплитам
   → Это НЕ жёсткое правило: неделя push+pull+legs+push+pull допустима (валидна)
   → Но предпочтительнее: push+pull+legs+bootcamp+push ИЛИ push+pull+legs+armBlast+pull
   → Исключение: если цель "масса" и фокус не на кардио — допустимо оставить чистый PPL-сплит

5. Прогрессия через разнообразие в Part 2 (недели 5-8):
   → Введи 1-2 НОВЫХ типа программ которых не было в Part 1
   → Увеличь сложность через вариативность, не только через частоту
   → Part 2 должен ЗАМЕТНО отличаться от Part 1 по составу программ

6. Учитывай фокусные области ОБЯЗАТЕЛЬНО:
   → Фокусная область атлета — это то, что ему ВАЖНО. НЕ игнорируй её.
   → Минимум 2-3 тренировки за 8 недель должны напрямую относиться к фокусной области
{self._format_focus_variety_instructions(user_profile.focus_areas, available_types)}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:

1. Соблюдай восстановление мышц между тренировками:
{self._format_recovery_rules(recovery_rules, user_profile.frequency)}

2. Используй ТОЛЬКО доступные типы программ из списка выше.
   ИСКЛЮЧЕНИЯ: НЕ используй education, assessment и endGame - это специальные программы (онбординг и финальные испытания), не для регулярных тренировочных планов.

3. Прогрессия нагрузки (КРИТИЧНО):
   - Недели 1-4 (part=1): ПОДГОТОВИТЕЛЬНЫЙ этап. Используй БОЛЬШЕ лёгких силовых:
     upperBody, fullBody, functionalFullBody (подготавливают тело к сложным сплитам).
     Push/pull допустимы, но НЕ больше чем в Part 2.
   - Недели 5-8 (part=2): ИНТЕНСИВНЫЙ этап. Используй БОЛЬШЕ тяжёлых сплитов:
     push, pull (изолированная нагрузка, требует подготовки).
   - ИЕРАРХИЯ СЛОЖНОСТИ силовых (от лёгкого к тяжёлому):
     fullBody/functionalFullBody (разгрузочные) → upperBody (подготовительная) → push/pull (тяжёлые сплиты)
   - Part 2 должен иметь БОЛЬШЕ push/pull тренировок, чем Part 1

4. Распределение тренировок по дням недели (зависит от частоты ЭТОЙ недели):
   - Если на неделе 3 тренировки: дни 1, 3, 5 (Пн, Ср, Пт)
   - Если на неделе 4 тренировки: дни 1, 2, 4, 5 (Пн, Вт, Чт, Пт)
   - Если на неделе 5 тренировок: дни 1, 2, 3, 5, 6 (Пн, Вт, Ср, Пт, Сб)
   - Если на неделе 6 тренировок: дни 1, 2, 3, 4, 6, 7 (Пн, Вт, Ср, Чт, Сб, Вс)
   ВАЖНО: Частота может быть РАЗНОЙ на разных неделях (см. ВОЛНООБРАЗНАЯ ПЕРИОДИЗАЦИЯ выше).
   Используй соответствующие дни для каждой недели в зависимости от её частоты.

5. Для каждого дня добавь 1-2 альтернативных типа программ в массив programSetTypes.
   - Первый элемент - основной тип программы
   - Следующие 1-2 элемента - альтернативы на случай занятости зала

6. КОМБО СИЛОВЫХ НА НЕДЕЛЕ:
   - КРИТИЧЕСКОЕ ПРАВИЛО: Если на неделе есть push или pull вместе с upperBody —
     ставь upperBody ПОСЛЕДНИМ СИЛОВЫМ в неделе (ближе к концу недели).
     upperBody = лёгкая/тонизирующая тренировка, ВСЕГДА идёт ПОСЛЕ тяжёлых push/pull.
     ЗАПРЕЩЕНО: ставить upperBody ПЕРЕД push или pull на той же неделе.
     Пример ОК: пн=push, ср=legs, пт=upperBody
     Пример BAD: пн=upperBody, ср=legs, пт=push ← upperBody перед push!
   - Если на неделе только 2 силовые тренировки → предпочтение: upperBody/fullBody + legs/gluteLab
     (комплексные, покрывают всё тело)
   - Если на неделе 3 силовые тренировки → предпочтение: push + pull + legs/gluteLab
     (классический сплит с полным покрытием мышечных групп)

7. НЕ СТАВЬ одинаковый ИЛИ конфликтующий тип тренировки на КОНЕЦ одной недели и НАЧАЛО следующей.
   Между последней тренировкой недели и первой следующей действуют ТЕ ЖЕ правила восстановления,
   что и внутри недели.
   Примеры ЗАПРЕЩЁННЫХ стыков:
   - ...пт=bootcamp] [пн=bootcamp... (одинаковый тип)
   - ...пт=pull] [пн=upperBody... (конфликт: те же мышцы)
   - ...пт=upperBody] [пн=push... (конфликт: те же мышцы)
   - ...пт=legs] [пн=gluteLab... (конфликт: те же мышцы)
   Примеры РАЗРЕШЁННЫХ стыков:
   - ...пт=pull] [пн=legs... (разные мышцы)
   - ...пт=bootcamp] [пн=push... (кардио → силовые OK)
   - ...пт=legs] [пн=metcon... (ноги → кардио OK)

8. После legs НЕЛЬЗЯ ставить bootcamp (ноги после legs перегружены, bootcamp даёт нагрузку на ноги).
   После legs МОЖНО: metcon, push, pull, upperBody, mindAndBody, reshape.

9. БАЛАНС push и pull:
   - Количество push и pull тренировок за 8 недель должно быть ОДИНАКОВЫМ (±1).
   - Исключение: если фокус атлета именно на спину (больше pull) или грудь (больше push).

10. Reshape — если доступен в клубе, поставь МИНИМУМ 1 тренировку за 8 недель.
    Reshape (пилатес на реформерах) полезен для глубоких мышц, осанки и восстановления.
    Если подходит по программе и цели (баланс, здоровье, восстановление) — можешь добавить больше.

{self._format_reshape_limit()}
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

    def _format_recovery_rules(self, recovery_rules: Dict[str, Dict], frequency: int = 3) -> str:
        """Форматировать правила восстановления для промпта."""

        header = (
            "   ПРАВИЛО: Два конфликтующих типа тренировок НЕЛЬЗЯ ставить ПОДРЯД "
            "(один сразу после другого в одной неделе).\n"
            "   Между конфликтующими типами должна быть минимум ОДНА другая тренировка.\n"
        )

        families = (
            "\n   ГРУППЫ КОНФЛИКТОВ (типы внутри группы нельзя ставить подряд):\n"
            "   a) Верх-силовые: push, pull, upperBody, armBlast\n"
            "      - push нельзя сразу после: push, upperBody, armBlast\n"
            "      - pull нельзя сразу после: pull, upperBody, armBlast\n"
            "      - upperBody нельзя сразу после: push, pull, upperBody, armBlast, fullBody, functionalFullBody (КОНФЛИКТУЕТ СО ВСЕМИ силовыми верха И всем телом!)\n"
            "      - armBlast нельзя сразу после: push, pull, upperBody, armBlast (КОНФЛИКТУЕТ СО ВСЕМИ силовыми верха!)\n"
            "      - ВАЖНО: push и pull НЕ конфликтуют между собой! push->pull и pull->push — ЭТО ОК.\n"
            "   b) Ноги: legs и gluteLab — нельзя подряд друг за другом\n"
            "      - ВАЖНО: после legs НЕЛЬЗЯ ставить bootcamp (ноги перегружены). После legs можно: metcon, push, pull, upperBody.\n"
            "      - bootcamp->legs — ОК (в обратном порядке можно).\n"
            "   c) Всё тело: fullBody и functionalFullBody — нельзя подряд друг за другом И нельзя подряд с upperBody\n"
            "   d) Кардио: bootcamp конфликтует ТОЛЬКО сам с собой, metcon ТОЛЬКО сам с собой\n"
            "      -> bootcamp->metcon — ОК, metcon->bootcamp — ОК\n"
            "   e) mindAndBody: НЕТ КОНФЛИКТОВ, можно ставить после чего угодно\n"
            "   f) reshape: конфликтует ТОЛЬКО сам с собой\n"
            "\n   КЛЮЧЕВОЙ ПРИЁМ: Используй legs, metcon, mindAndBody как \"разделители\"\n"
            "   между push/pull и upperBody/armBlast.\n"
            "   bootcamp можно как разделитель, НО не сразу после legs.\n"
        )

        examples = self._get_schedule_examples(max(frequency, 3))

        return header + families + examples

    def _get_schedule_examples(self, frequency: int) -> str:
        """Конкретные примеры валидных/невалидных расписаний для заданной частоты."""

        if frequency == 3:
            return (
                "\n   ПРИМЕРЫ РАСПИСАНИЙ (3 тренировки: дни 1, 3, 5):\n"
                "   OK:  день1=push,     день3=legs,      день5=pull\n"
                "   OK:  день1=bootcamp,  день3=legs,      день5=bootcamp\n"
                "   BAD: день1=push,      день3=upperBody,  день5=pull  <- upperBody сразу после push!\n"
            )
        elif frequency == 4:
            return (
                "\n   ПРИМЕРЫ РАСПИСАНИЙ (4 тренировки: дни 1, 2, 4, 5):\n"
                "   OK:  день1=push,  день2=legs,       день4=pull,      день5=bootcamp\n"
                "   OK:  день1=push,  день2=legs,       день4=pull,      день5=metcon\n"
                "   BAD: день1=push,  день2=upperBody,  день4=legs,      день5=pull  <- upperBody сразу после push!\n"
                "   FIX: день1=push,  день2=legs,       день4=upperBody, день5=bootcamp  <- legs разделяет push и upperBody\n"
            )
        elif frequency == 5:
            return (
                "\n   ПРИМЕРЫ РАСПИСАНИЙ (5 тренировок: дни 1, 2, 3, 5, 6):\n"
                "   OK:  день1=push,  день2=legs,      день3=pull,     день5=bootcamp, день6=upperBody\n"
                "   OK:  день1=push,  день2=bootcamp,  день3=pull,     день5=legs,     день6=metcon\n"
                "   OK:  день1=legs,  день2=push,      день3=bootcamp, день5=pull,     день6=upperBody\n"
                "   BAD: день1=push,  день2=legs,      день3=pull,     день5=upperBody, день6=bootcamp  <- upperBody сразу после pull!\n"
                "   FIX: день1=push,  день2=legs,      день3=pull,     день5=bootcamp,  день6=upperBody  <- поменяли день5 и день6 местами\n"
            )
        else:  # frequency >= 6
            return (
                "\n   ПРИМЕРЫ РАСПИСАНИЙ (6 тренировок: дни 1, 2, 3, 4, 6, 7):\n"
                "   OK:  день1=push,  день2=legs,    день3=pull,     день4=bootcamp, день6=upperBody, день7=metcon\n"
                "   OK:  день1=legs,  день2=push,    день3=metcon,   день4=pull,     день6=bootcamp,  день7=gluteLab\n"
                "   BAD: день1=push,  день2=pull,    день3=upperBody, день4=legs,    день6=bootcamp,  день7=metcon  <- upperBody сразу после pull!\n"
                "   FIX: день1=push,  день2=legs,    день3=pull,      день4=bootcamp, день6=upperBody, день7=metcon  <- legs разделяет push и pull\n"
            )

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

    def _format_reshape_limit(self) -> str:
        """Reshape — без лимита, минимум 1 за блок указан в правилах выше."""
        return ''

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
- Приоритет: Bootcamp и Metcon (высокий расход калорий), НО не более 45% от всех тренировок
- ОБЯЗАТЕЛЬНО: силовые (Legs, Full Body, Functional Full Body) для сохранения мышц — минимум 25%
- Постепенное увеличение интенсивности, не частоты кардио
- Баланс: ~40% кардио + ~35% силовые + ~25% функциональные/восстановление
""")

        # Спортивная форма + масса
        if user_profile.body_type == 'спортивное' and user_profile.goal == 'масса':
            instructions.append("""
ВАЖНО: Набор массы при спортивной форме:
- Приоритет: Push, Pull, Legs (силовой сплит) — основа плана
- ОБЯЗАТЕЛЬНО: 1 тренировка Bootcamp или Metcon каждые 2 недели для здоровья сердца
- Добавь GluteLab, ArmBlast для разнообразия и изоляции отстающих мышц
- Upper и Full Body для дополнительного объёма
- НЕ делай более 3 силовых подряд без кардио/функциональной разгрузки
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

        fix_suggestions = self._generate_fix_suggestions(validation_errors)

        retry_prompt = f"""{original_prompt}

ОШИБКИ В ПРЕДЫДУЩЕЙ ПОПЫТКЕ (ИСПРАВЬ ВСЕ):
{errors_text}

{fix_suggestions}

НАПОМИНАНИЕ О ПРАВИЛЕ ВОССТАНОВЛЕНИЯ:
Два конфликтующих типа НЕЛЬЗЯ ставить ПОДРЯД в одной неделе.
Проверь КАЖДУЮ неделю: для каждой тренировки посмотри на ПРЕДЫДУЩУЮ тренировку в той же неделе.
Если предыдущая тренировка в списке конфликтов текущей — ПОМЕНЯЙ ПОРЯДОК или ЗАМЕНИ тип.

СПОСОБЫ ИСПРАВЛЕНИЯ нарушений восстановления:
1. ПОМЕНЯЙ МЕСТАМИ две соседние тренировки в неделе
2. ВСТАВЬ "разделитель" (legs, bootcamp, metcon, mindAndBody) между конфликтующими типами
3. ЗАМЕНИ один из конфликтующих типов на неконфликтующий

Верни ПОЛНЫЙ исправленный JSON массив:
"""
        return retry_prompt

    def _generate_fix_suggestions(self, validation_errors: List[str]) -> str:
        """Парсит ошибки валидации и генерирует конкретные подсказки для исправления."""
        import re

        suggestions = []

        for error in validation_errors:
            if 'нарушение восстановления' in error:
                match = re.match(
                    r"Неделя (\d+), день (\d+): нарушение восстановления для '(\w+)'\. "
                    r"Слишком рано после предыдущих тренировок: (.+)",
                    error
                )
                if match:
                    week = match.group(1)
                    day = match.group(2)
                    problem_type = match.group(3)
                    prev_types_str = match.group(4)
                    last_prev = prev_types_str.split(', ')[-1].strip()

                    suggestions.append(
                        f"-> Неделя {week}, день {day}: '{problem_type}' стоит сразу после '{last_prev}', "
                        f"а они конфликтуют. РЕШЕНИЕ: поменяй день {day} с предыдущим днём местами, "
                        f"или замени '{problem_type}' на тип без конфликта с '{last_prev}' "
                        f"(например: legs, bootcamp, metcon, mindAndBody)."
                    )

        if suggestions:
            return "КОНКРЕТНЫЕ ПОДСКАЗКИ ДЛЯ ИСПРАВЛЕНИЯ:\n" + '\n'.join(suggestions)
        return ""
