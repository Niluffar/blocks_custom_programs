"""
Data models для структуры recommendedPlan и tasksProgress
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class RecommendedPlanItem:
    """Один элемент recommendedPlan - тренировка на конкретный день"""
    text: str  # "Выполни тренировку BootCamp"
    week: int  # 1-8
    day: int  # 1-7 (пн-вс)
    programSetTypes: List[str]  # ['bootcamp', 'metcon'] - основной + альтернативы
    part: int  # 1 или 2 (первая/вторая месячная программа)

    def to_dict(self) -> Dict:
        """Конвертировать в словарь для MongoDB"""
        return {
            'text': self.text,
            'week': self.week,
            'day': self.day,
            'programSetTypes': self.programSetTypes,
            'part': self.part
        }


@dataclass
class TaskProgressItem:
    """Один элемент tasksProgress - цель по типу программы"""
    text: str  # "Выполни 4 тренировки BootCamp"
    programSetTypes: List[str]  # ['bootcamp']
    part: int  # 1 или 2
    target: int  # количество тренировок для выполнения
    done: int = 0  # сколько уже выполнено
    week: int = 1  # первая неделя где встречается этот тип

    def to_dict(self) -> Dict:
        """Конвертировать в словарь для MongoDB"""
        return {
            'text': self.text,
            'programSetTypes': self.programSetTypes,
            'part': self.part,
            'target': self.target,
            'done': self.done,
            'week': self.week
        }


@dataclass
class GeneratedPlan:
    """Полный сгенерированный план для блока"""
    recommendedPlan: List[RecommendedPlanItem]
    tasksProgress: List[TaskProgressItem]
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Конвертировать в словарь для MongoDB"""
        return {
            'recommendedPlan': [item.to_dict() for item in self.recommendedPlan],
            'tasksProgress': [task.to_dict() for task in self.tasksProgress],
            'metadata': self.metadata
        }
