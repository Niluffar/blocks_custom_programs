"""
Главный оркестратор генерации планов тренировок
Координирует все модули и вызывает Gemini API для создания
персонализированных recommendedPlan и tasksProgress
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

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


# Настройка логирования
logging.basicConfig(level=logging.INFO)
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

    def __init__(self, gemini_api_key: Optional[str] = None, context_file_path: Optional[str] = None):
        """
        Инициализация генератора.

        Args:
            gemini_api_key: API ключ для Gemini (опционально, берётся из .env)
            context_file_path: Путь к "Контекст Путъ Атлета.md" (опционально)
        """
        # Инициализация компонентов
        self.user_analyzer = UserProfileAnalyzer()
        self.club_filter = ClubFilter()
        self.tasks_generator = TasksGenerator()
        self.prompt_builder = PromptBuilder()
        self.validator = PlanValidator()

        # Инициализация загрузчика паттернов
        if context_file_path is None:
            # По умолчанию ищем в текущей директории проекта
            project_root = Path(__file__).parent.parent
            context_file_path = project_root / "Контекст Путъ Атлета.md"

        try:
            self.pattern_loader = PatternLoader(str(context_file_path))
            self.pattern_loader.load_all_patterns()
            logger.info(f"Загружено {len(self.pattern_loader.patterns)} паттернов из контекстного файла")
        except FileNotFoundError:
            logger.warning(f"Файл паттернов не найден: {context_file_path}. Генерация будет без примеров.")
            self.pattern_loader = None

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

        # Лимит Reshape на этот блок (рассчитано из pilatesVisits / кол-во блоков в абонементе)
        reshape_per_block = club_data.get('reshape_per_block', 0)

        logger.info(f"Клуб: {club_data.get('club_name', 'Не указан')}, "
                   f"Доступно программ: {len(available_types)}, "
                   f"Reshape на блок: {reshape_per_block}")

        # Если reshape_per_block = 0 — убрать reshape из доступных типов
        if reshape_per_block <= 0:
            available_types = [t for t in available_types if t != 'reshape']

        # Финальная проверка что после всех фильтраций остались программы
        if not available_types:
            logger.error("После фильтрации не осталось доступных программ")
            raise ValueError(
                f"После фильтрации не осталось доступных программ для клуба {club_data.get('club_name')}. "
                f"Проверьте конфигурацию клуба и programsets."
            )

        # 3. Получить примеры паттернов для промпта
        pattern_examples = []
        if self.pattern_loader:
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
            reshape_per_block=reshape_per_block
        )

        # 5. Генерация плана через LLM с валидацией
        logger.info("Этап 5: Генерация плана через Gemini API")
        recommended_plan = self._generate_with_llm(
            prompt=prompt,
            user_profile=user_profile,
            available_types=available_types,
            max_attempts=max_attempts,
            reshape_per_block=reshape_per_block
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
        reshape_per_block: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Генерация плана через LLM с валидацией и повторными попытками.

        Args:
            prompt: Промпт для LLM
            user_profile: Профиль пользователя
            available_types: Доступные типы программ
            max_attempts: Максимальное количество попыток
            reshape_per_block: Лимит тренировок Reshape на этот блок

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

                # Валидация
                is_valid, errors = self.validator.validate_plan(
                    plan=plan,
                    recovery_rules=RECOVERY_RULES,
                    available_types=available_types,
                    frequency=user_profile.frequency,
                    reshape_per_block=reshape_per_block
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
                continue

        # Если после всех попыток не получилось
        raise Exception(
            f"LLM не смог сгенерировать валидный план после {max_attempts} попыток. "
            "Проверьте промпт и правила валидации."
        )

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
