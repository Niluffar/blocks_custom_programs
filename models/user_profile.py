"""
Data models для профиля пользователя
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class UserProfile:
    """Полный профиль пользователя для генерации плана"""

    # Основные данные из анкеты
    gender: str  # male/female
    age: int
    height: int  # см
    weight: float  # кг
    body_type: str  # худощавое/среднее/плотное/спортивное/полное
    goal: str  # похудение/масса/рельеф/здоровье/поддержание
    focus_areas: List[str]  # верх_тела, ноги, выносливость, баланс
    experience_level: str  # новичок/любитель/профи
    current_break: int  # дни с последней тренировки
    health_restrictions: str = ''  # Raw text ограничений здоровья

    # Данные из InBody
    body_composition: Optional[Dict] = None  # BMI, fat%, muscle mass, etc.

    # Рассчитанные параметры
    frequency: int = 3  # базовая частота 3-5 тренировок в неделю
    weekly_schedule: List[int] = field(default_factory=lambda: [3]*8)  # частота по неделям [W1..W8]

    # История
    historical_frequency: float = 0.0  # реальная частота посещений
    marathon_history: Dict = field(default_factory=dict)
    progression_level: str = 'beginner'  # beginner/intermediate/advanced

    # Клуб и зоны
    club_id: Optional[str] = None
    available_zones: List[str] = field(default_factory=list)


@dataclass
class HistoryAnalysis:
    """Анализ истории посещений и марафонов"""
    total_visits: int = 0
    avg_per_week: float = 0.0
    consistency_score: float = 0.0

    # Марафоны
    total_completed: int = 0
    success_rate: float = 0.0
    medals: List[str] = field(default_factory=list)
    avg_attendance: float = 0.0


@dataclass
class ClubData:
    """Данные о клубе пользователя"""
    club_id: Optional[str] = None
    zones: List[str] = field(default_factory=list)
    load_factors: Dict[str, float] = field(default_factory=dict)
    capacities: Dict[str, int] = field(default_factory=dict)
