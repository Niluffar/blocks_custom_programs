"""
Анализ истории посещений и марафонов пользователя
Используется ТОЛЬКО для определения:
- Реальной частоты тренировок
- Уровня прогрессии атлета (beginner/intermediate/advanced)
- Консистентности посещений

НЕ используется для определения предпочтений типов программ!
Фокус на цели и оптимальном плане, а не на том что атлет любит.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta


class HistoryAnalyzer:
    """
    Анализирует историю посещений и марафонов для определения:
    - Реальной частоты тренировок (не завышать ожидания)
    - Уровня опыта и прогрессии (beginner/intermediate/advanced)
    - Консистентности тренировок

    НЕ анализирует предпочтения по типам программ!
    """

    def analyze_checkins(
        self,
        checkins: List[Dict[str, Any]],
        period_months: int = 3
    ) -> Dict[str, Any]:
        """
        Анализ посещений за последние N месяцев (только частота и консистентность).

        Args:
            checkins: Список посещений с датами
            period_months: Период анализа в месяцах (по умолчанию 3)

        Returns:
            Dict с показателями:
            - total_visits: общее количество посещений
            - avg_per_week: средняя частота в неделю
            - consistency_score: оценка регулярности (0.0-1.0)
        """
        if not checkins:
            return {
                'total_visits': 0,
                'avg_per_week': 0.0,
                'consistency_score': 0.0
            }

        # Фильтрация по периоду (если checkins содержат даты)
        filtered_checkins = self._filter_by_period(checkins, period_months)

        total_visits = len(filtered_checkins)
        weeks = period_months * 4  # Примерно 4 недели в месяце
        avg_per_week = total_visits / weeks if weeks > 0 else 0.0

        # Расчёт консистентности (регулярность посещений)
        consistency_score = self._calculate_consistency(filtered_checkins, weeks)

        return {
            'total_visits': total_visits,
            'avg_per_week': round(avg_per_week, 1),
            'consistency_score': round(consistency_score, 2)
        }

    def analyze_marathons(
        self,
        marathons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Анализ истории марафонов (для определения уровня опыта).

        Args:
            marathons: Список марафонов пользователя

        Returns:
            Dict с показателями:
            - total_completed: количество завершённых марафонов
            - success_rate: процент успешного завершения
            - medals: список медалей
            - avg_attendance: средняя посещаемость
        """
        if not marathons:
            return {
                'total_completed': 0,
                'success_rate': 0.0,
                'medals': [],
                'avg_attendance': 0.0
            }

        # Завершённые марафоны
        completed = [m for m in marathons if m.get('status') == 'completed']
        total_completed = len(completed)

        # Процент успешности
        success_rate = total_completed / len(marathons) if marathons else 0.0

        # Медали
        medals = [m.get('medal') for m in completed if m.get('medal')]

        # Средняя посещаемость
        avg_attendance = self._calculate_avg_attendance(completed)

        return {
            'total_completed': total_completed,
            'success_rate': round(success_rate, 2),
            'medals': medals,
            'avg_attendance': round(avg_attendance, 2)
        }

    def calculate_progression_level(
        self,
        marathon_stats: Dict[str, Any],
        checkin_stats: Dict[str, Any]
    ) -> str:
        """
        Определить уровень прогрессии на основе истории марафонов и посещений.

        Args:
            marathon_stats: Статистика по марафонам из analyze_marathons()
            checkin_stats: Статистика по посещениям из analyze_checkins()

        Returns:
            str: beginner | intermediate | advanced
        """
        # Если нет истории - новичок
        if marathon_stats['total_completed'] == 0 and checkin_stats['total_visits'] == 0:
            return 'beginner'

        # Подсчёт золотых медалей
        gold_medals = sum(1 for m in marathon_stats['medals'] if m == 'gold')

        # Критерии для advanced:
        # - 3+ завершённых марафона
        # - 2+ золотых медали
        # - Посещаемость 80%+
        # - Консистентность 0.7+
        if (marathon_stats['total_completed'] >= 3 and
            gold_medals >= 2 and
            marathon_stats['avg_attendance'] >= 0.8 and
            checkin_stats['consistency_score'] >= 0.7):
            return 'advanced'

        # Критерии для intermediate:
        # - 1+ завершённый марафон
        # - Посещаемость 60%+
        # - ИЛИ регулярные посещения 3+ раза в неделю
        if (marathon_stats['total_completed'] >= 1 and
            marathon_stats['avg_attendance'] >= 0.6):
            return 'intermediate'

        if checkin_stats['avg_per_week'] >= 3.0 and checkin_stats['consistency_score'] >= 0.6:
            return 'intermediate'

        # Иначе - новичок
        return 'beginner'

    def _filter_by_period(
        self,
        checkins: List[Dict[str, Any]],
        period_months: int
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать посещения по периоду времени.

        Args:
            checkins: Список посещений
            period_months: Период в месяцах

        Returns:
            Отфильтрованный список посещений
        """
        # Если checkins не содержат дату, возвращаем как есть
        if not checkins or 'date' not in checkins[0]:
            return checkins

        # Вычисляем дату отсечки
        cutoff_date = datetime.now() - timedelta(days=period_months * 30)

        filtered = []
        for checkin in checkins:
            checkin_date = checkin.get('date')

            # Попытка преобразовать в datetime если это строка
            if isinstance(checkin_date, str):
                try:
                    checkin_date = datetime.fromisoformat(checkin_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue

            # Если дата после отсечки - включаем
            if isinstance(checkin_date, datetime) and checkin_date >= cutoff_date:
                filtered.append(checkin)

        return filtered

    def _calculate_consistency(
        self,
        checkins: List[Dict[str, Any]],
        total_weeks: int
    ) -> float:
        """
        Рассчитать консистентность посещений (регулярность по неделям).

        Высокий score (0.8-1.0) = регулярные посещения каждую неделю
        Низкий score (0.0-0.3) = нерегулярные посещения

        Args:
            checkins: Список посещений
            total_weeks: Общее количество недель в периоде

        Returns:
            float: Оценка консистентности от 0.0 до 1.0
        """
        if not checkins or total_weeks == 0:
            return 0.0

        # Группировка по неделям
        weeks_with_visits = set()

        for checkin in checkins:
            checkin_date = checkin.get('date')

            if isinstance(checkin_date, str):
                try:
                    checkin_date = datetime.fromisoformat(checkin_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue

            if isinstance(checkin_date, datetime):
                # ISO week number
                week_num = checkin_date.isocalendar()[1]
                year = checkin_date.year
                weeks_with_visits.add((year, week_num))

        # Процент недель с посещениями
        weeks_coverage = len(weeks_with_visits) / total_weeks if total_weeks > 0 else 0.0

        return min(weeks_coverage, 1.0)

    def _calculate_avg_attendance(
        self,
        completed_marathons: List[Dict[str, Any]]
    ) -> float:
        """
        Рассчитать среднюю посещаемость по завершённым марафонам.

        Args:
            completed_marathons: Список завершённых марафонов

        Returns:
            float: Средняя посещаемость (0.0-1.0)
        """
        if not completed_marathons:
            return 0.0

        attendance_rates = []

        for marathon in completed_marathons:
            # Попытка получить attendance_rate
            rate = marathon.get('attendance_rate')

            if rate is not None:
                attendance_rates.append(float(rate))
            else:
                # Если нет attendance_rate, можно рассчитать из completed/total
                completed_workouts = marathon.get('completed_workouts', 0)
                total_workouts = marathon.get('total_workouts', 1)

                if total_workouts > 0:
                    rate = completed_workouts / total_workouts
                    attendance_rates.append(rate)

        if not attendance_rates:
            return 0.0

        avg = sum(attendance_rates) / len(attendance_rates)
        return min(avg, 1.0)
