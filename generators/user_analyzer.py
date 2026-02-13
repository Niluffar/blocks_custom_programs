"""
Анализ профиля пользователя для генерации recommendedPlan
Определяет частоту тренировок, уровень опыта и приоритеты на основе анкеты,
InBody данных, истории посещений и истории марафонов
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from models.user_profile import UserProfile
from generators.history_analyzer import HistoryAnalyzer


class UserProfileAnalyzer:
    """
    Анализирует профиль пользователя и определяет параметры для генерации плана.

    Использует:
    - Анкету пользователя (цель, опыт, фокус, ограничения)
    - InBody данные (состав тела)
    - Историю посещений (реальная частота)
    - Историю марафонов (уровень прогрессии)
    """

    def __init__(self):
        self.history_analyzer = HistoryAnalyzer()

    def analyze(
        self,
        questionnaire: Dict[str, Any],
        inbody_data: Optional[Dict[str, Any]] = None,
        checkins: Optional[List[Dict[str, Any]]] = None,
        marathons: Optional[List[Dict[str, Any]]] = None
    ) -> UserProfile:
        """
        Полный анализ профиля пользователя.

        Args:
            questionnaire: Данные из анкеты пользователя
            inbody_data: Данные InBody теста (опционально)
            checkins: История посещений за последние 3 месяца (опционально)
            marathons: История марафонов (опционально)

        Returns:
            UserProfile с рассчитанными параметрами
        """
        # Базовые данные из анкеты
        goal = self._extract_goal(questionnaire)
        focus_areas = self._extract_focus(questionnaire)
        experience_level = self._determine_experience(questionnaire)
        health_restrictions = self._process_restrictions(questionnaire)
        current_break = self._extract_break_duration(questionnaire)

        # Анализ истории для определения реального уровня
        checkin_stats = self.history_analyzer.analyze_checkins(checkins) if checkins else {'avg_per_week': 0.0, 'consistency_score': 0.0}
        marathon_stats = self.history_analyzer.analyze_marathons(marathons) if marathons else {'total_completed': 0, 'avg_attendance': 0.0}

        historical_frequency = checkin_stats['avg_per_week']
        progression_level = self.history_analyzer.calculate_progression_level(marathon_stats, checkin_stats)

        # Расчёт целевой частоты (3-5 тренировок в неделю)
        frequency = self._calculate_frequency(
            questionnaire=questionnaire,
            historical_frequency=historical_frequency,
            progression_level=progression_level,
            experience_level=experience_level,
            goal=goal,
            health_restrictions=health_restrictions,
            current_break=current_break
        )

        # Анализ состава тела из InBody
        body_composition = self._analyze_inbody(inbody_data) if inbody_data else {}

        # Извлечение базовых данных
        gender = questionnaire.get('gender', 'male')
        age = questionnaire.get('age', 30)
        height = questionnaire.get('height', 170)
        weight = questionnaire.get('weight', 70)
        current_form = questionnaire.get('current_form', 'среднее')

        # Волнообразная периодизация: понедельный график частот
        weekly_schedule = self._build_weekly_schedule(
            base_frequency=frequency,
            progression_level=progression_level,
            experience_level=experience_level,
            goal=goal,
            current_break=current_break
        )

        return UserProfile(
            gender=gender,
            age=age,
            height=height,
            weight=weight,
            body_type=current_form,  # current_form из анкеты → body_type в модели
            goal=goal,
            focus_areas=focus_areas,
            experience_level=experience_level,
            frequency=frequency,
            weekly_schedule=weekly_schedule,
            health_restrictions=health_restrictions,
            body_composition=body_composition,
            current_break=current_break,
            historical_frequency=historical_frequency,
            progression_level=progression_level
        )

    def _calculate_frequency(
        self,
        questionnaire: Dict[str, Any],
        historical_frequency: float,
        progression_level: str,
        experience_level: str,
        goal: str,
        health_restrictions: List[str],
        current_break: int
    ) -> int:
        """
        Рассчитать целевую частоту тренировок (3-5 в неделю).

        Логика основана на:
        - Уровень опыта из анкеты
        - Реальная частота из истории посещений
        - Успешность прохождения марафонов
        - Цель и текущая форма
        - Ограничения по здоровью
        - Длительность перерыва

        Returns:
            int: Частота от 3 до 5 тренировок в неделю
        """
        # Базовая частота для новичков
        base_frequency = 3

        # УВЕЛИЧЕНИЕ частоты

        # По опыту из анкеты
        if experience_level == 'профи':
            base_frequency += 2
        elif experience_level == 'любитель':
            base_frequency += 1

        # По цели:
        # - Масса НЕ требует высокой частоты — мышцы растут во время отдыха,
        #   важнее интенсивность и восстановление. 4 тренировки/неделю — оптимум.
        # - Рельеф и похудение выигрывают от чуть большей частоты (больше расход калорий)
        if goal in ['рельеф', 'похудение']:
            base_frequency += 1

        # По текущей форме (если уже спортивный и тренируется)
        current_form = questionnaire.get('current_form', '').lower()
        if current_form == 'спортивное' and current_break <= 30:
            base_frequency += 1

        # По реальной истории посещений (если ходит регулярно 4+ раза)
        if historical_frequency >= 4.0:
            base_frequency += 1
        elif historical_frequency >= 3.5:
            pass  # Нормальный уровень
        elif historical_frequency > 0 and historical_frequency <= 2.0:
            base_frequency -= 1  # Низкая активность

        # По истории марафонов (успешное прохождение = может больше)
        if progression_level == 'advanced':
            base_frequency += 1
        elif progression_level == 'beginner' and historical_frequency > 0:
            # Новичок но с историей посещений - не завышаем
            base_frequency -= 1

        # СНИЖЕНИЕ частоты

        # Если новичок - начинаем с 3
        if experience_level == 'новичок':
            base_frequency = min(base_frequency, 3)

        # Длительный перерыв (более 3 месяцев)
        if current_break > 90:
            base_frequency -= 1

        # Ограничения по здоровью
        if health_restrictions:
            base_frequency -= 1

        # Полная форма + цель похудение (щадящий режим)
        if current_form == 'полное' and goal == 'похудение':
            base_frequency = min(base_frequency, 4)  # Не больше 4

        # Потолок частоты:
        # - 5 только для advanced (подтверждённый опытом уровень)
        # - Для остальных макс 4 — достаточно для любой цели, меньше риск перетренированности
        max_freq = 5 if progression_level == 'advanced' else 4
        frequency = max(3, min(max_freq, base_frequency))

        return frequency

    def _build_weekly_schedule(
        self,
        base_frequency: int,
        progression_level: str,
        experience_level: str,
        goal: str,
        current_break: int
    ) -> List[int]:
        """
        Построить понедельный график частот (волнообразная периодизация).

        Принципы:
        - Неделя 4 и 8: deload (разгрузка, -1 тренировка от базы)
        - Part 1 (W1-4): адаптация/наращивание → deload
        - Part 2 (W5-8): пиковая нагрузка → deload
        - Новички (freq=3): ровный график без волн (телу и так хватает стресса)
        - Для опытных: волна base → base+1 → base → base-1 (deload)

        Clamp: каждую неделю от 3 до 5 тренировок.

        Returns:
            List[int] из 8 элементов — частота для каждой недели
        """
        f = base_frequency

        # Новички или возврат после долгого перерыва — ровный график, только deload на 4/8
        if experience_level in ('новичок', 'beginner') or current_break > 90:
            if f <= 3:
                # Для новичков на 3 — ровно, deload не нужен (и так минимум)
                return [3] * 8
            schedule = [f, f, f, max(f - 1, 3), f, f, f, max(f - 1, 3)]
            return schedule

        # Базовая частота 3: мягкая волна — одна нагрузочная неделя на каждую часть
        # W3 и W7 — по 4 тренировки (микро-перегрузка), остальные по 3
        if f == 3:
            schedule = [3, 3, 4, 3, 3, 3, 4, 3]
            return schedule

        # Базовая частота 4: волна (4, 4, 5, 3, 4, 5, 5, 3)
        if f == 4:
            # Part 1: адаптация
            # Part 2: прогрессия с пиком на W6-W7
            schedule = [4, 4, 5, 3, 4, 5, 5, 3]
            return schedule

        # Базовая частота 5: волна (5, 5, 5, 4, 5, 5, 5, 4)
        # При 5 тренировках/неделю повышать нельзя — уже максимум
        # Deload на W4 и W8 до 4
        if f == 5:
            schedule = [5, 5, 5, 4, 5, 5, 5, 4]
            return schedule

        # Fallback
        schedule = [f] * 8
        schedule[3] = max(f - 1, 3)
        schedule[7] = max(f - 1, 3)
        return schedule

    def _extract_goal(self, questionnaire: Dict[str, Any]) -> str:
        """
        Извлечь основную цель из анкеты.

        Returns:
            str: похудение | масса | рельеф | здоровье | поддержание
        """
        goal = questionnaire.get('goal', 'здоровье').lower()

        # Маппинг возможных вариантов
        goal_mapping = {
            'похудение': 'похудение',
            'снижение веса': 'похудение',
            'жиросжигание': 'похудение',
            'burn': 'похудение',

            'масса': 'масса',
            'набор массы': 'масса',
            'мышцы': 'масса',
            'build': 'масса',
            'strong': 'масса',

            'рельеф': 'рельеф',
            'тонус': 'рельеф',
            'fit body': 'рельеф',
            'форма': 'рельеф',

            'здоровье': 'здоровье',
            'athlete': 'здоровье',
            'выносливость': 'здоровье',

            'поддержание': 'поддержание',
            'поддержка': 'поддержание'
        }

        return goal_mapping.get(goal, 'здоровье')

    def _extract_focus(self, questionnaire: Dict[str, Any]) -> List[str]:
        """
        Извлечь дополнительные фокусные области из анкеты.

        Returns:
            List[str]: Список фокусов (верх_тела, ноги, выносливость, баланс)
        """
        focus_raw = questionnaire.get('focus', [])

        if isinstance(focus_raw, str):
            focus_raw = [focus_raw]

        focus_areas = []

        for f in focus_raw:
            f_lower = f.lower()

            if any(kw in f_lower for kw in ['верх', 'upper', 'грудь', 'спина', 'руки', 'плечи']):
                focus_areas.append('верх_тела')
            elif any(kw in f_lower for kw in ['ноги', 'legs', 'ягодицы', 'glute', 'попа']):
                focus_areas.append('ноги')
            elif any(kw in f_lower for kw in ['выносливость', 'кардио', 'cardio', 'metcon', 'bootcamp']):
                focus_areas.append('выносливость')
            elif any(kw in f_lower for kw in ['баланс', 'гибкость', 'координация', 'mind', 'yoga', 'пилатес']):
                focus_areas.append('баланс')

        # По умолчанию баланс
        if not focus_areas:
            focus_areas.append('баланс')

        return list(set(focus_areas))  # Убираем дубликаты

    def _determine_experience(self, questionnaire: Dict[str, Any]) -> str:
        """
        Определить уровень опыта из анкеты.

        Returns:
            str: новичок | любитель | профи
        """
        experience = questionnaire.get('experience', 'новичок').lower()

        experience_mapping = {
            'новичок': 'новичок',
            'начинающий': 'новичок',
            'beginner': 'новичок',

            'любитель': 'любитель',
            'средний': 'любитель',
            'intermediate': 'любитель',

            'профи': 'профи',
            'продвинутый': 'профи',
            'advanced': 'профи',
            'pro': 'профи'
        }

        return experience_mapping.get(experience, 'новичок')

    def _process_restrictions(self, questionnaire: Dict[str, Any]) -> List[str]:
        """
        Обработать ограничения по здоровью из анкеты.

        Returns:
            List[str]: Список ограничений
        """
        restrictions_raw = questionnaire.get('health_restrictions', [])

        if isinstance(restrictions_raw, str):
            restrictions_raw = [restrictions_raw]

        restrictions = []

        for r in restrictions_raw:
            r_lower = r.lower()

            if any(kw in r_lower for kw in ['протрузия', 'грыжа', 'позвоночник', 'спина']):
                restrictions.append('протрузия/грыжа')
            elif any(kw in r_lower for kw in ['сустав', 'колено', 'плечо', 'локоть']):
                restrictions.append('травмы_суставов')
            elif any(kw in r_lower for kw in ['давление', 'сердце', 'кардио']):
                restrictions.append('кардио_ограничения')
            else:
                restrictions.append(r)

        return list(set(restrictions))

    def _extract_break_duration(self, questionnaire: Dict[str, Any]) -> int:
        """
        Извлечь длительность перерыва в тренировках (в днях).

        Returns:
            int: Количество дней без тренировок
        """
        break_days = questionnaire.get('current_break', 0)

        # Если указано в других единицах
        break_unit = questionnaire.get('break_unit', 'days')

        if break_unit == 'weeks':
            break_days *= 7
        elif break_unit == 'months':
            break_days *= 30

        return int(break_days)


    def _analyze_inbody(self, inbody_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Анализировать данные InBody теста.

        Args:
            inbody_data: Данные теста (жир, мышцы, BMI и т.д.)

        Returns:
            Dict с ключевыми показателями
        """
        return {
            'body_fat_percentage': inbody_data.get('body_fat_percentage', 0.0),
            'muscle_mass': inbody_data.get('muscle_mass', 0.0),
            'bmi': inbody_data.get('bmi', 0.0),
            'visceral_fat': inbody_data.get('visceral_fat', 0.0)
        }
