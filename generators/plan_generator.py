"""
Главный оркестратор генерации планов тренировок
Координирует все модули и вызывает Gemini API для создания
персонализированных recommendedPlan и tasksProgress
"""
import os
import json
import copy
import time
import logging
from typing import Dict, List, Optional, Any

# Gemini API
import google.generativeai as genai

# Внутренние модули
from generators.user_analyzer import UserProfileAnalyzer
from generators.club_filter import ClubFilter
from generators.tasks_generator import TasksGenerator
from utils.prompt_builder import PromptBuilder
from utils.plan_validator import PlanValidator
from utils.pattern_loader import PatternLoader
from rules.recovery_rules import RECOVERY_RULES


logger = logging.getLogger(__name__)


class RecommendedPlanGenerator:
    """
    Главный оркестратор генерации планов тренировок.

    Процесс генерации:
    1. Анализ профиля пользователя (user_analyzer)
    2. Фильтрация программ по клубу (club_filter)
    3. Построение промпта для LLM (prompt_builder)
    4. Генерация плана через Gemini API
    5. Валидация плана (plan_validator)
    6. Генерация tasksProgress (tasks_generator)
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Инициализация генератора.

        Args:
            gemini_api_key: API ключ для Gemini (опционально, берётся из .env)
        """
        # Инициализация компонентов
        self.user_analyzer = UserProfileAnalyzer()
        self.club_filter = ClubFilter()
        self.tasks_generator = TasksGenerator()
        self.prompt_builder = PromptBuilder()
        self.validator = PlanValidator()

        # Инициализация загрузчика паттернов
        self.pattern_loader = PatternLoader()
        self.pattern_loader.load_all_patterns()
        logger.info(f"Загружено {len(self.pattern_loader.patterns)} паттернов")

        # Инициализация Gemini API
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY не найден. LLM генерация будет недоступна.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            # Используем gemini-2.5-pro
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            logger.info("Gemini API инициализирован (модель: gemini-2.5-pro)")

    def generate(
        self,
        user_id: str,
        questionnaire_data: Dict[str, Any],
        inbody_data: Optional[Dict[str, Any]] = None,
        checkins_data: Optional[List[Dict[str, Any]]] = None,
        marathons_data: Optional[List[Dict[str, Any]]] = None,
        heropass_data: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Генерировать recommendedPlan и tasksProgress.

        Args:
            user_id: ID пользователя
            questionnaire_data: Данные анкеты
            inbody_data: Данные InBody теста (опционально)
            checkins_data: История посещений (опционально)
            marathons_data: История марафонов (опционально)
            heropass_data: Данные HeroPass для определения клуба (опционально)
            max_attempts: Максимальное количество попыток генерации

        Returns:
            Dict с recommendedPlan, tasksProgress и метаданными
        """
        logger.info(f"Начало генерации плана для пользователя {user_id}")

        # 1. Анализ пользователя
        logger.info("Этап 1: Анализ профиля пользователя")
        user_profile = self.user_analyzer.analyze(
            questionnaire=questionnaire_data,
            inbody_data=inbody_data,
            checkins=checkins_data,
            marathons=marathons_data
        )

        logger.info(f"Профиль: цель={user_profile.goal}, частота={user_profile.frequency}, "
                   f"weekly_schedule={user_profile.weekly_schedule}, "
                   f"опыт={user_profile.experience_level}, прогрессия={user_profile.progression_level}")

        # 2. Получить доступные программы в клубе (из РЕАЛЬНЫХ programsets в MongoDB)
        logger.info("Этап 2: Получение доступных программ из клуба")

        try:
            club_data = self.club_filter.get_user_club_data(user_id, heropass_data)
        except ValueError as e:
            # Нет активного HeroPass
            logger.error(f"Невозможно сгенерировать план: {e}")
            raise ValueError(
                f"Генерация плана невозможна для пользователя {user_id}. "
                f"Причина: нет активного HeroPass (абонемента)."
            ) from e

        # Получить реальные доступные типы программ из programsets
        available_types = club_data.get('available_program_types', [])

        # Проверка что есть доступные программы
        if not available_types:
            logger.error(f"В клубе {club_data.get('club_name')} нет доступных программ")
            raise ValueError(
                f"В клубе {club_data.get('club_name')} ({club_data.get('club_id')}) "
                f"не найдено ни одной доступной программы. Проверьте programsets в MongoDB."
            )

        # Reshape: если доступен в клубе — оставляем, лимит больше не ограничиваем
        reshape_per_block = 0  # Без лимита

        logger.info(f"Клуб: {club_data.get('club_name', 'Не указан')}, "
                   f"Доступно программ: {len(available_types)}")

        # Финальная проверка что после всех фильтраций остались программы
        if not available_types:
            logger.error("После фильтрации не осталось доступных программ")
            raise ValueError(
                f"После фильтрации не осталось доступных программ для клуба {club_data.get('club_name')}. "
                f"Проверьте конфигурацию клуба и programsets."
            )

        # 3. Получить примеры паттернов для промпта
        pattern_examples = self.pattern_loader.get_example_patterns_for_prompt(
            goal=user_profile.goal,
            experience_level=user_profile.experience_level,
            max_examples=5
        )
        logger.info(f"Выбрано {len(pattern_examples)} примеров паттернов для промпта")

        # 4. Построить промпт для LLM
        logger.info("Этап 4: Построение промпта для LLM")
        prompt = self.prompt_builder.build_prompt(
            user_profile=user_profile,
            available_types=available_types,
            recovery_rules=RECOVERY_RULES,
            pattern_examples=pattern_examples,
            reshape_per_block=reshape_per_block,
            weekly_schedule=user_profile.weekly_schedule
        )

        # 5. Генерация плана через LLM с валидацией
        logger.info("Этап 5: Генерация плана через Gemini API")
        recommended_plan = self._generate_with_llm(
            prompt=prompt,
            user_profile=user_profile,
            available_types=available_types,
            max_attempts=max_attempts,
            reshape_per_block=reshape_per_block,
            weekly_schedule=user_profile.weekly_schedule
        )

        logger.info(f"План сгенерирован: {len(recommended_plan)} тренировок")

        # 6. Генерация tasksProgress
        logger.info("Этап 6: Генерация tasksProgress")
        tasks_progress = self.tasks_generator.generate(recommended_plan)

        logger.info(f"Задачи созданы: {len(tasks_progress)} задач")

        # 7. Валидация соответствия tasks и plan
        validation = self.tasks_generator.validate_tasks_against_plan(
            tasks_progress,
            recommended_plan
        )

        if not validation['is_valid']:
            logger.warning(f"Несоответствие tasks и plan: {validation['errors']}")

        # Результат
        result = {
            'recommendedPlan': recommended_plan,
            'tasksProgress': tasks_progress,
            'metadata': {
                'user_id': user_id,
                'frequency': user_profile.frequency,
                'weekly_schedule': user_profile.weekly_schedule,
                'historical_frequency': user_profile.historical_frequency,
                'progression_level': user_profile.progression_level,
                'goal': user_profile.goal,
                'focus_areas': user_profile.focus_areas,
                'club_id': club_data.get('club_id'),
                'club_name': club_data.get('club_name'),
                'available_program_types': available_types,  # Реальные programsets из MongoDB
                'reshape_per_block': reshape_per_block,
                'total_workouts': len(recommended_plan),
                'total_tasks': len(tasks_progress)
            }
        }

        logger.info("Генерация завершена успешно")
        return result

    def _generate_with_llm(
        self,
        prompt: str,
        user_profile: Any,
        available_types: List[str],
        max_attempts: int = 3,
        reshape_per_block: int = 0,
        weekly_schedule: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерация плана через LLM с валидацией и повторными попытками.

        Args:
            prompt: Промпт для LLM
            user_profile: Профиль пользователя
            available_types: Доступные типы программ
            max_attempts: Максимальное количество попыток
            reshape_per_block: Лимит тренировок Reshape на этот блок
            weekly_schedule: Понедельный график частот [W1..W8]

        Returns:
            Валидный recommendedPlan

        Raises:
            Exception: Если не удалось сгенерировать валидный план
        """
        if not self.model:
            raise Exception("Gemini API не инициализирован. Проверьте GEMINI_API_KEY.")

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Попытка генерации {attempt}/{max_attempts}")

            try:
                # Вызов Gemini API
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()

                # Попытка извлечь JSON
                plan = self._extract_json(response_text)

                if not plan:
                    logger.warning(f"Попытка {attempt}: не удалось распарсить JSON")
                    continue

                # Автоисправление порядка тренировок внутри недель
                plan = self._auto_fix_recovery(plan)

                # Автоисправление позиции upperBody (после push/pull)
                plan = self._auto_fix_upper_position(plan)

                # Валидация
                is_valid, errors = self.validator.validate_plan(
                    plan=plan,
                    recovery_rules=RECOVERY_RULES,
                    available_types=available_types,
                    frequency=user_profile.frequency,
                    reshape_per_block=reshape_per_block,
                    weekly_schedule=weekly_schedule,
                    goal=user_profile.goal
                )

                if is_valid:
                    logger.info(f"План валиден с попытки {attempt}")
                    return plan

                # Если не валиден - логируем ошибки
                logger.warning(f"Попытка {attempt}: план не прошёл валидацию")
                for error in errors[:5]:  # Первые 5 ошибок
                    logger.warning(f"  - {error}")

                # Модифицируем промпт с указанием ошибок
                prompt = self.prompt_builder.build_retry_prompt(prompt, errors)

            except json.JSONDecodeError as e:
                logger.warning(f"Попытка {attempt}: ошибка парсинга JSON: {e}")
                continue

            except Exception as e:
                logger.error(f"Попытка {attempt}: неожиданная ошибка: {e}")
                if attempt < max_attempts:
                    delay = 2 ** attempt  # 2, 4, 8 сек
                    logger.info(f"Ожидание {delay} сек перед следующей попыткой...")
                    time.sleep(delay)
                continue

        # Если после всех попыток не получилось
        raise Exception(
            f"LLM не смог сгенерировать валидный план после {max_attempts} попыток. "
            "Проверьте промпт и правила валидации."
        )

    def _auto_fix_upper_position(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Автоисправление позиции upperBody: если на неделе есть push/pull,
        upperBody должен стоять ПОСЛЕ них (ближе к концу недели).
        Меняет местами содержимое слотов (programSetTypes + text), не трогая day/week.
        """
        plan = copy.deepcopy(plan)

        for week_num in range(1, 9):
            week_indices = [
                i for i, w in enumerate(plan) if w.get('week') == week_num
            ]
            if not week_indices:
                continue

            # Сортируем по дню
            week_indices.sort(key=lambda i: plan[i].get('day', 0))

            types = [
                plan[i]['programSetTypes'][0]
                for i in week_indices
                if plan[i].get('programSetTypes')
            ]

            if 'upperBody' not in types:
                continue
            if 'push' not in types and 'pull' not in types:
                continue

            upper_pos = types.index('upperBody')
            last_hard_pos = max(
                (j for j, t in enumerate(types) if t in ('push', 'pull')),
                default=-1
            )

            if upper_pos >= last_hard_pos:
                continue  # Уже OK

            # Переставляем: вынимаем upper и вставляем после последнего push/pull
            upper_idx = week_indices[upper_pos]
            target_idx = week_indices[last_hard_pos]

            # Сохраняем содержимое upper
            upper_content = {
                'programSetTypes': plan[upper_idx]['programSetTypes'],
                'text': plan[upper_idx]['text']
            }

            # Сдвигаем содержимое вниз (от upper_pos+1 до last_hard_pos)
            for j in range(upper_pos, last_hard_pos):
                src = week_indices[j + 1]
                dst = week_indices[j]
                plan[dst]['programSetTypes'] = plan[src]['programSetTypes']
                plan[dst]['text'] = plan[src]['text']

            # Ставим upper на место last_hard_pos
            plan[target_idx]['programSetTypes'] = upper_content['programSetTypes']
            plan[target_idx]['text'] = upper_content['text']

            logger.info(f"Auto-fix: неделя {week_num} — upperBody перемещён в конец (после push/pull)")

        return plan

    def _extract_json(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Извлечь JSON из ответа LLM.

        LLM может вернуть JSON с дополнительным текстом или в markdown блоке.

        Args:
            response_text: Текст ответа от LLM

        Returns:
            Распарсенный JSON или None
        """
        # Убираем markdown блоки если есть
        text = response_text.strip()

        # Убираем ```json ... ``` если есть
        if text.startswith('```json'):
            text = text[7:]  # Убираем ```json
        if text.startswith('```'):
            text = text[3:]   # Убираем ```

        if text.endswith('```'):
            text = text[:-3]   # Убираем ```

        text = text.strip()

        # Попытка найти JSON массив
        start_idx = text.find('[')
        end_idx = text.rfind(']')

        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Если не получилось - пробуем парсить весь текст
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _auto_fix_recovery(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Автоисправление нарушений восстановления путём переупорядочивания тренировок внутри недели.

        Не меняет типы тренировок — только переставляет их между слотами дней.
        Дни (1,2,3,5,6) остаются фиксированными, меняется только содержимое (programSetTypes, text).

        Returns:
            Исправленный план (или оригинал, если исправление невозможно)
        """
        from rules.recovery_rules import can_perform

        plan = copy.deepcopy(plan)

        for week_num in range(1, 9):
            # Индексы тренировок этой недели в общем плане
            week_entries = [
                (i, w) for i, w in enumerate(plan)
                if w.get('week') == week_num
            ]
            if not week_entries:
                continue

            # Сортируем по дню
            week_entries.sort(key=lambda x: x[1].get('day', 0))

            # Проверяем есть ли нарушения
            types_list = [
                w['programSetTypes'][0]
                for _, w in week_entries
                if w.get('programSetTypes')
            ]

            has_violation = False
            for i in range(len(types_list)):
                if not can_perform(types_list[i], types_list[:i]):
                    has_violation = True
                    break

            if not has_violation:
                continue

            # Ищем валидную перестановку
            valid_order = self._find_valid_ordering(types_list)

            if valid_order is None:
                logger.warning(
                    f"Auto-fix: неделя {week_num} — невозможно найти валидный порядок "
                    f"для типов {types_list}"
                )
                continue

            # Собираем содержимое тренировок (programSetTypes + text)
            workout_contents = [
                {
                    'programSetTypes': week_entries[i][1]['programSetTypes'],
                    'text': week_entries[i][1]['text']
                }
                for i in range(len(week_entries))
            ]

            # Переставляем содержимое согласно найденному порядку
            reordered = [workout_contents[i] for i in valid_order]

            for pos, content in enumerate(reordered):
                plan_idx = week_entries[pos][0]
                plan[plan_idx]['programSetTypes'] = content['programSetTypes']
                plan[plan_idx]['text'] = content['text']

            logger.info(f"Auto-fix: неделя {week_num} переупорядочена для соблюдения восстановления")

        return plan

    def _find_valid_ordering(self, types: List[str]) -> Optional[List[int]]:
        """
        Найти перестановку индексов, удовлетворяющую правилам восстановления.
        Использует backtracking. Безопасно для списков до 5 элементов (макс 120 перестановок).

        Args:
            types: Список типов тренировок в исходном порядке

        Returns:
            Список индексов в валидном порядке, или None если невозможно
        """
        from rules.recovery_rules import can_perform

        n = len(types)

        def backtrack(used: set, current_order: list) -> Optional[list]:
            if len(current_order) == n:
                return current_order[:]

            prev_types = [types[i] for i in current_order]

            for i in range(n):
                if i in used:
                    continue
                if can_perform(types[i], prev_types):
                    used.add(i)
                    current_order.append(i)
                    result = backtrack(used, current_order)
                    if result is not None:
                        return result
                    current_order.pop()
                    used.discard(i)

            return None

        return backtrack(set(), [])

    def get_generation_stats(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Получить статистику по сгенерированному плану.

        Args:
            result: Результат генерации

        Returns:
            Статистика
        """
        plan = result.get('recommendedPlan', [])
        tasks = result.get('tasksProgress', [])

        # Распределение по типам
        type_distribution = {}
        for workout in plan:
            if 'programSetTypes' in workout and workout['programSetTypes']:
                ptype = workout['programSetTypes'][0]
                type_distribution[ptype] = type_distribution.get(ptype, 0) + 1

        # Распределение по неделям
        weekly_distribution = {}
        for week in range(1, 9):
            week_workouts = [w for w in plan if w.get('week') == week]
            weekly_distribution[f'week_{week}'] = len(week_workouts)

        return {
            'total_workouts': len(plan),
            'total_tasks': len(tasks),
            'part1_workouts': len([w for w in plan if w.get('part') == 1]),
            'part2_workouts': len([w for w in plan if w.get('part') == 2]),
            'type_distribution': type_distribution,
            'weekly_distribution': weekly_distribution,
            'frequency': result['metadata'].get('frequency')
        }
