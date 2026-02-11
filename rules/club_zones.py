"""
Маппинг клубов, зон и типов программ на основе реальной структуры Hero Fitness
Данные основаны на документах 'Контекст Программы.txt' и 'Контекст Путъ Атлета.txt'
"""
from typing import Dict, List

# Маппинг зон к типам программ
# Основано на реальной структуре залов из контекстных документов
ZONE_TO_PROGRAM_TYPES: Dict[str, List[str]] = {
    # FFB/Upper зона - функциональный зал и верх тела
    'ffb_upper': [
        'upperBody',           # Upper программы
        'functionalFullBody',  # Functional Full Body
        'push',                # Push
        'pull',                # Pull
        'armBlast',            # Arms
        'assessment'           # Assessment
    ],

    # Legs зона - ноги и ягодицы
    'legs': [
        'legs',                # Legs программы
        'gluteLab'             # Glute программы
    ],

    # Bootcamp зона
    'bootcamp': [
        'bootcamp'             # Bootcamp программы
    ],

    # Metcon зона - метаболическое кондиционирование
    'metcon': [
        'metcon'               # Metcon (Cardio, Power, Core)
    ],

    # Mind Body зона - йога и пилатес
    'mind_body': [
        'mindAndBody'          # Pilates и другие Mind&Body
    ],

    # Full Body зона (специфичная для Villa)
    'full_body': [
        'upperBody',           # Upper
        'push',                # Push
        'pull',                # Pull
        'armBlast',            # Arms
        'legs',                # Legs
        'gluteLab',            # Glute
        'assessment',          # Assessment
        'fullBody'             # Full Body программы
    ],

    # Reshape зона (Villa, HJ 4You) - пилатес на реформерах
    'reshape': [
        'reshape'              # Reshape программы
    ],

    # Assessment зона (HJ 4You)
    'assessment': [
        'assessment'           # Assessment программы
    ]
}

# Обратный маппинг: тип программы -> возможные зоны
PROGRAM_TYPE_TO_ZONES: Dict[str, List[str]] = {
    'upperBody': ['ffb_upper', 'full_body'],
    'functionalFullBody': ['ffb_upper'],
    'push': ['ffb_upper', 'full_body'],
    'pull': ['ffb_upper', 'full_body'],
    'armBlast': ['ffb_upper', 'full_body'],
    'legs': ['legs', 'full_body'],
    'gluteLab': ['legs', 'full_body'],
    'bootcamp': ['bootcamp'],
    'metcon': ['metcon'],
    'mindAndBody': ['mind_body'],
    'fullBody': ['full_body'],
    'reshape': ['reshape'],  # Reshape - пилатес на реформерах (Villa, HJ 4You)
    'assessment': ['ffb_upper', 'full_body', 'assessment'],
    'education': [],  # Теория не требует зоны
}

# Структура клубов с доступными зонами и вместимостью
CLUB_STRUCTURE: Dict[str, Dict] = {
    'Nurly-Orda': {
        'zones': ['ffb_upper', 'legs', 'bootcamp'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 14,
            'bootcamp': 24
        },
        'load_factors': {
            # Будет заполнено из реальных данных или по умолчанию 0.5
            'ffb_upper': 0.5,
            'legs': 0.5,
            'bootcamp': 0.5
        }
    },

    'Europa City': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp', 'mind_body'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 30,
            'metcon': 24,
            'bootcamp': 28,
            'mind_body': 17
        },
        'load_factors': {
            'ffb_upper': 0.5,
            'legs': 0.5,
            'metcon': 0.5,
            'bootcamp': 0.5,
            'mind_body': 0.5
        }
    },

    'Colibri': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 30,
            'metcon': 24,
            'bootcamp': 32
        },
        'load_factors': {
            'ffb_upper': 0.5,
            'legs': 0.5,
            'metcon': 0.5,
            'bootcamp': 0.5
        }
    },

    # Aliases для клубов (как они называются в БД)
    'HJ Colibri': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 30,
            'metcon': 24,
            'bootcamp': 32
        },
        'load_factors': {
            'ffb_upper': 0.5,
            'legs': 0.5,
            'metcon': 0.5,
            'bootcamp': 0.5
        }
    },

    'Promenade': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 30,
            'metcon': 24,
            'bootcamp': 28
        },
        'load_factors': {
            'ffb_upper': 0.5,
            'legs': 0.5,
            'metcon': 0.5,
            'bootcamp': 0.5
        }
    },

    'Villa': {
        'zones': ['full_body', 'reshape', 'bootcamp'],
        'capacities': {
            'full_body': 48,
            'reshape': 15,
            'bootcamp': 24
        },
        'load_factors': {
            'full_body': 0.5,
            'reshape': 0.5,
            'bootcamp': 0.5
        }
    },

    'HJ 4You': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp', 'reshape', 'assessment'],
        'capacities': {
            'ffb_upper': 32,
            'legs': 30,
            'metcon': 24,
            'bootcamp': 30,
            'reshape': 16,
            'assessment': 20  # Примерная вместимость
        },
        'load_factors': {
            'ffb_upper': 0.5,
            'legs': 0.5,
            'metcon': 0.5,
            'bootcamp': 0.5,
            'reshape': 0.5,
            'assessment': 0.5
        }
    },

    # Дополнительные aliases на случай других названий в БД
    'HJ Nurly-Orda': {
        'zones': ['ffb_upper', 'legs', 'bootcamp'],
        'capacities': {'ffb_upper': 32, 'legs': 14, 'bootcamp': 24},
        'load_factors': {'ffb_upper': 0.5, 'legs': 0.5, 'bootcamp': 0.5}
    },
    'HJ Europa City': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp', 'mind_body'],
        'capacities': {'ffb_upper': 32, 'legs': 30, 'metcon': 24, 'bootcamp': 28, 'mind_body': 17},
        'load_factors': {'ffb_upper': 0.5, 'legs': 0.5, 'metcon': 0.5, 'bootcamp': 0.5, 'mind_body': 0.5}
    },
    'HJ Promenade': {
        'zones': ['ffb_upper', 'legs', 'metcon', 'bootcamp'],
        'capacities': {'ffb_upper': 32, 'legs': 30, 'metcon': 24, 'bootcamp': 28},
        'load_factors': {'ffb_upper': 0.5, 'legs': 0.5, 'metcon': 0.5, 'bootcamp': 0.5}
    },
    'HJ Villa': {
        'zones': ['full_body', 'reshape', 'bootcamp'],
        'capacities': {'full_body': 48, 'reshape': 15, 'bootcamp': 24},
        'load_factors': {'full_body': 0.5, 'reshape': 0.5, 'bootcamp': 0.5}
    }
}

# Все возможные зоны в системе Hero Fitness
ALL_ZONES = [
    'ffb_upper',      # FFB/Upper зона - функциональный зал
    'legs',           # Legs зона - ноги и ягодицы
    'bootcamp',       # Bootcamp зона
    'metcon',         # Metcon зона - кардио и метаболизм
    'mind_body',      # Mind Body зона - йога и пилатес
    'full_body',      # Full Body зона (Villa)
    'reshape',        # Reshape зона (Villa, HJ 4You)
    'assessment'      # Assessment зона (HJ 4You)
]


def get_club_zones(club_name: str) -> List[str]:
    """
    Получить список доступных зон для клуба.

    Args:
        club_name: Название клуба

    Returns:
        Список доступных зон
    """
    club_data = CLUB_STRUCTURE.get(club_name, {})
    return club_data.get('zones', ALL_ZONES)  # По умолчанию все зоны


def get_club_capacities(club_name: str) -> Dict[str, int]:
    """
    Получить вместимость зон клуба.

    Args:
        club_name: Название клуба

    Returns:
        Словарь {зона: вместимость}
    """
    club_data = CLUB_STRUCTURE.get(club_name, {})
    return club_data.get('capacities', {})


def get_club_load_factors(club_name: str) -> Dict[str, float]:
    """
    Получить load factors зон клуба.

    Args:
        club_name: Название клуба

    Returns:
        Словарь {зона: load_factor}
    """
    club_data = CLUB_STRUCTURE.get(club_name, {})
    return club_data.get('load_factors', {})


def get_available_program_types(club_name: str) -> List[str]:
    """
    Получить список доступных типов программ для клуба.

    Args:
        club_name: Название клуба

    Returns:
        Список типов программ
    """
    zones = get_club_zones(club_name)
    program_types = set()

    for zone in zones:
        zone_programs = ZONE_TO_PROGRAM_TYPES.get(zone, [])
        program_types.update(zone_programs)

    return list(program_types)


def can_perform_in_club(program_type: str, club_name: str) -> bool:
    """
    Проверить, можно ли выполнить программу в данном клубе.

    Args:
        program_type: Тип программы
        club_name: Название клуба

    Returns:
        True если программа доступна в клубе
    """
    required_zones = PROGRAM_TYPE_TO_ZONES.get(program_type, [])

    # Если зоны не требуются (education), программа доступна везде
    if not required_zones:
        return True

    available_zones = get_club_zones(club_name)

    # Программа доступна если хотя бы одна из требуемых зон есть в клубе
    return any(zone in available_zones for zone in required_zones)


def get_zone_availability_score(zone: str, club_name: str) -> float:
    """
    Рассчитать score доступности зоны (учитывает load factor и capacity).
    Высокий score = менее загружена и больше вместимость.

    Args:
        zone: Название зоны
        club_name: Название клуба

    Returns:
        Score доступности (0.0 - 1.0)
    """
    capacities = get_club_capacities(club_name)
    load_factors = get_club_load_factors(club_name)

    capacity = capacities.get(zone, 20)  # По умолчанию средняя вместимость
    load = load_factors.get(zone, 0.5)   # По умолчанию средняя загрузка

    # Нормализуем capacity относительно baseline=20
    normalized_capacity = capacity / 20.0

    # Score = (1 - загрузка) * нормализованная_вместимость
    score = (1.0 - load) * normalized_capacity

    return min(score, 1.0)  # Clamp to 1.0


def rank_program_types_by_availability(
    program_types: List[str],
    club_name: str
) -> Dict[str, float]:
    """
    Ранжировать типы программ по доступности в клубе.

    Args:
        program_types: Список типов программ
        club_name: Название клуба

    Returns:
        Словарь {тип_программы: availability_score}
    """
    scores = {}

    for ptype in program_types:
        required_zones = PROGRAM_TYPE_TO_ZONES.get(ptype, [])

        if not required_zones:
            # Нет требований к зонам - максимальный score
            scores[ptype] = 1.0
            continue

        # Средняя доступность всех возможных зон для этого типа
        zone_scores = []
        for zone in required_zones:
            if zone in get_club_zones(club_name):
                zone_scores.append(get_zone_availability_score(zone, club_name))

        if zone_scores:
            scores[ptype] = sum(zone_scores) / len(zone_scores)
        else:
            scores[ptype] = 0.0  # Недоступен в этом клубе

    return scores


def get_all_clubs() -> List[str]:
    """
    Получить список всех клубов в системе.

    Returns:
        Список названий клубов
    """
    return list(CLUB_STRUCTURE.keys())
