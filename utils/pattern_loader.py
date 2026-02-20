"""
Паттерны тренировок для различных целей и уровней.
Используются как примеры в промпте для LLM.
"""
from typing import List, Dict, Any, Optional


class PatternLoader:
    """
    Паттерны тренировок для путей:
    - Burn 1-5 (похудение)
    - Fit Body 1-5 (рельеф)
    - Legs 1-5 (ноги)
    - Build/Strong 1-5 (масса)
    - Athlete 1-5 (здоровье)
    """

    def __init__(self, context_file_path: str = None):
        self.patterns = []

    def load_all_patterns(self) -> List[Dict[str, Any]]:
        """Загрузить все паттерны."""
        self.patterns = []
        self.patterns.extend(self._extract_burn_patterns())
        self.patterns.extend(self._extract_fit_body_patterns())
        self.patterns.extend(self._extract_legs_patterns())
        self.patterns.extend(self._extract_build_patterns())
        self.patterns.extend(self._extract_athlete_patterns())
        return self.patterns

    def _extract_burn_patterns(self) -> List[Dict[str, Any]]:
        """Извлечь паттерны Burn 1-5."""
        patterns = []

        # Burn Level 1
        patterns.append({
            'path': 'Burn',
            'level': 1,
            'weeks': 4,
            'frequency': '3-4',
            'description': 'Мягкий вход в режим жиросжигания. Формируем привычку 3-4 раза в неделю.',
            'pattern': 'Full Body + Bootcamp + Metcon чередуются. Bootcamp и Metcon дают интервальную нагрузку, Full Body и Upper - силовую базу.',
            'goal': 'похудение',
            'target_types': ['bootcamp', 'metcon', 'fullBody', 'upperBody']
        })

        # Burn Level 2
        patterns.append({
            'path': 'Burn',
            'level': 2,
            'weeks': 4,
            'frequency': '4',
            'description': 'Усилить жиросжигание за счёт большего объёма и добавить акцент на нижнюю часть тела.',
            'pattern': 'Bootcamp + Legs/Glute + Metcon + Upper. Появляется обязательный блок Legs/Glute для высокого энергозатрата.',
            'goal': 'похудение',
            'target_types': ['bootcamp', 'metcon', 'legs', 'gluteLab', 'upperBody', 'fullBody']
        })

        # Burn Level 3
        patterns.append({
            'path': 'Burn',
            'level': 3,
            'weeks': 4,
            'frequency': '4-5',
            'description': 'Связать жиросжигание с более серьёзной силовой структурой (Push/Pull + Legs/Glute).',
            'pattern': 'Push/Pull + Bootcamp + Legs/Glute + Metcon. Вводим сплит Push/Pull для осознанной силовой работы. Чередование тяжёлых (5 тренировок) и лёгких недель.',
            'goal': 'похудение',
            'target_types': ['push', 'pull', 'bootcamp', 'metcon', 'legs', 'gluteLab', 'fullBody']
        })

        # Burn Level 4
        patterns.append({
            'path': 'Burn',
            'level': 4,
            'weeks': 6,
            'frequency': '4-5',
            'description': 'Высокий объём, высокая интенсивность. Серьёзный этап для подготовленных атлетов.',
            'pattern': 'Много Bootcamp + Metcon для высокого расхода энергии. Upper/Legs/Glute и Push/Pull не дают просесть по силе.',
            'goal': 'похудение',
            'target_types': ['bootcamp', 'metcon', 'upperBody', 'legs', 'gluteLab', 'push', 'pull']
        })

        # Burn Level 5
        patterns.append({
            'path': 'Burn',
            'level': 5,
            'weeks': 8,
            'frequency': '4-6',
            'description': 'Максимальный уровень жиросжигания. Высокая частота тренировок и интенсивность.',
            'pattern': 'Чередование "лёгких" недель (4 тренировки: Bootcamp + Upper + Legs/Glute) и "тяжёлых" недель (6 тренировок: Metcon + Push/Pull + Bootcamp + Legs/Glute).',
            'goal': 'похудение',
            'target_types': ['bootcamp', 'metcon', 'upperBody', 'legs', 'gluteLab', 'push', 'pull']
        })

        return patterns

    def _extract_fit_body_patterns(self) -> List[Dict[str, Any]]:
        """Извлечь паттерны Fit Body 1-5."""
        patterns = []

        # Fit Body Level 1
        patterns.append({
            'path': 'Fit Body',
            'level': 1,
            'weeks': 4,
            'frequency': '3-4',
            'description': 'Подтянуть тело, добавить тонус. База для тех, кто хочет просто выглядеть лучше.',
            'pattern': 'Full Body + Upper + Bootcamp + Legs/Glute. Умный general fitness: форма, тонус, немного выносливости.',
            'goal': 'рельеф',
            'target_types': ['fullBody', 'upperBody', 'bootcamp', 'legs', 'gluteLab', 'metcon']
        })

        # Fit Body Level 2
        patterns.append({
            'path': 'Fit Body',
            'level': 2,
            'weeks': 4,
            'frequency': '4',
            'description': 'Больше тонуса, больше формы. Переход к силовому сплиту с акцентом на верх/низ и руки.',
            'pattern': 'Push/Pull + Legs/Glute + Arms + Bootcamp/Metcon. Полноценный силовой сплит с визуальным акцентом на руки.',
            'goal': 'рельеф',
            'target_types': ['push', 'pull', 'legs', 'gluteLab', 'armBlast', 'bootcamp', 'metcon', 'upperBody']
        })

        # Fit Body Level 3
        patterns.append({
            'path': 'Fit Body',
            'level': 3,
            'weeks': 4,
            'frequency': '4-5',
            'description': 'Усилить силовую базу, добавить акценты на ноги/ягодицы и руки.',
            'pattern': 'Чёткий ритм: верх + низ (Upper/Push-Pull + Legs/Glute) почти в каждой неделе. Arms остаётся как визуальный апгрейд.',
            'goal': 'рельеф',
            'target_types': ['upperBody', 'push', 'pull', 'legs', 'gluteLab', 'armBlast', 'bootcamp', 'metcon']
        })

        # Fit Body Level 4
        patterns.append({
            'path': 'Fit Body',
            'level': 4,
            'weeks': 6,
            'frequency': '4-5',
            'description': 'Максимально "собрать" тело: силовой каркас, форма, тонус, плюс выносливость.',
            'pattern': 'Чередуются два типа недель: Metcon-недели (Metcon + Upper + Legs/Glute) и Сплит-недели (Push/Pull + Legs/Glute + Upper).',
            'goal': 'рельеф',
            'target_types': ['metcon', 'upperBody', 'legs', 'gluteLab', 'push', 'pull', 'bootcamp']
        })

        # Fit Body Level 5
        patterns.append({
            'path': 'Fit Body',
            'level': 5,
            'weeks': 8,
            'frequency': '4-6',
            'description': 'Максимум формы: плотный силовой сплит плюс поддерживающее кардио.',
            'pattern': 'Чёткий паттерн: нечётные недели - Bootcamp + Metcon + Upper (4 тренировки); чётные недели - жёсткий силовой (Push/Pull + Legs/Glute, 5-6 тренировок).',
            'goal': 'рельеф',
            'target_types': ['bootcamp', 'metcon', 'upperBody', 'push', 'pull', 'legs', 'gluteLab']
        })

        return patterns

    def _extract_legs_patterns(self) -> List[Dict[str, Any]]:
        """Извлечь паттерны Legs 1-5."""
        patterns = []

        # Legs Level 1-5
        for level in range(1, 6):
            if level == 1:
                patterns.append({
                    'path': 'Legs',
                    'level': 1,
                    'weeks': 4,
                    'frequency': '3-4',
                    'description': 'Акцент на нижнюю часть тела (ноги и ягодицы), первый визуальный эффект.',
                    'pattern': 'Legs/Glute каждую неделю 1-2 раза + Full Body/Upper для баланса + Bootcamp/Metcon для кардио.',
                    'goal': 'рельеф',
                    'target_types': ['legs', 'gluteLab', 'fullBody', 'upperBody', 'bootcamp', 'metcon']
                })
            elif level == 2:
                patterns.append({
                    'path': 'Legs',
                    'level': 2,
                    'weeks': 4,
                    'frequency': '4',
                    'description': 'Усилить акцент на ноги и ягодицы. Legs/Glute 3 раза в неделю.',
                    'pattern': 'Legs/Glute 3 раза в неделю - чёткий сигнал. Upper/Full Body держат верх в тонусе.',
                    'goal': 'рельеф',
                    'target_types': ['legs', 'gluteLab', 'upperBody', 'fullBody', 'bootcamp', 'metcon']
                })
            elif level == 3:
                patterns.append({
                    'path': 'Legs',
                    'level': 3,
                    'weeks': 4,
                    'frequency': '4-5',
                    'description': 'Ноги и ягодицы как основной приоритет + серьёзный силовой сплит по верху.',
                    'pattern': 'Legs/Glute 2-3 раза в неделю + Push/Pull и Upper для баланса + Metcon/Bootcamp для кардио.',
                    'goal': 'рельеф',
                    'target_types': ['legs', 'gluteLab', 'push', 'pull', 'upperBody', 'bootcamp', 'metcon']
                })
            elif level == 4:
                patterns.append({
                    'path': 'Legs',
                    'level': 4,
                    'weeks': 6,
                    'frequency': '4-5',
                    'description': 'Максимальный фокус на ноги и ягодицы. Для тех, кто живёт в Legs-зале.',
                    'pattern': 'Legs/Glute 2 раза в неделю стабильно. Push/Pull и Upper держат верх, Bootcamp/Metcon добавляют кардио.',
                    'goal': 'рельеф',
                    'target_types': ['legs', 'gluteLab', 'push', 'pull', 'upperBody', 'bootcamp', 'metcon']
                })
            elif level == 5:
                patterns.append({
                    'path': 'Legs',
                    'level': 5,
                    'weeks': 8,
                    'frequency': '4-6',
                    'description': 'Максимальный акцент на ноги и ягодицы с высокой общей нагрузкой.',
                    'pattern': 'Чередование: Bootcamp-недели (Bootcamp + Legs/Glute + Metcon + Legs/Glute) и Сплит-недели (Legs/Glute + Push/Pull чередуются + Upper).',
                    'goal': 'рельеф',
                    'target_types': ['legs', 'gluteLab', 'bootcamp', 'metcon', 'push', 'pull', 'upperBody']
                })

        return patterns

    def _extract_build_patterns(self) -> List[Dict[str, Any]]:
        """Извлечь паттерны Build/Strong 1-5."""
        patterns = []

        # Build Level 1-5
        for level in range(1, 6):
            if level == 1:
                patterns.append({
                    'path': 'Build',
                    'level': 1,
                    'weeks': 4,
                    'frequency': '3-4',
                    'description': 'Силовая база для набора мышц и плотности. Старт силового пути.',
                    'pattern': 'Full Body + Upper + Legs/Glute + Push/Pull. Равномерная силовая по всему телу с минимумом Metcon/Bootcamp.',
                    'goal': 'масса',
                    'target_types': ['fullBody', 'upperBody', 'legs', 'gluteLab', 'push', 'pull', 'metcon']
                })
            elif level == 2:
                patterns.append({
                    'path': 'Build',
                    'level': 2,
                    'weeks': 4,
                    'frequency': '4',
                    'description': 'Нормальный силовой сплит: верх+низ с приоритетом мышечной массы.',
                    'pattern': 'Push/Pull 2-3 раза в неделю + Legs/Glute + Arms. Кардио остаётся фоном (1 раз Metcon/Bootcamp).',
                    'goal': 'масса',
                    'target_types': ['push', 'pull', 'legs', 'gluteLab', 'armBlast', 'metcon', 'bootcamp']
                })
            elif level == 3:
                patterns.append({
                    'path': 'Build',
                    'level': 3,
                    'weeks': 4,
                    'frequency': '4-5',
                    'description': 'Силовой тренинг как основа: много верха, стабильный низ, акцент на руки.',
                    'pattern': 'Push/Pull 2 раза в неделю каждую неделю + Legs/Glute 1 раз + Arms. Metcon/Bootcamp только для кондиций.',
                    'goal': 'масса',
                    'target_types': ['push', 'pull', 'legs', 'gluteLab', 'armBlast', 'metcon', 'bootcamp']
                })
            elif level == 4:
                patterns.append({
                    'path': 'Build',
                    'level': 4,
                    'weeks': 6,
                    'frequency': '4-5',
                    'description': 'Максимально структурированный силовой: много верха, регулярные ноги/ягодицы, акцент на руки.',
                    'pattern': 'Чередуются Upper-недели (Upper + Arms + Legs/Glute) и Push/Pull-недели (двойной Push/Pull + Legs/Glute + Upper).',
                    'goal': 'масса',
                    'target_types': ['upperBody', 'push', 'pull', 'legs', 'gluteLab', 'armBlast', 'metcon', 'bootcamp']
                })
            elif level == 5:
                patterns.append({
                    'path': 'Build',
                    'level': 5,
                    'weeks': 8,
                    'frequency': '4-6',
                    'description': 'Максимум силового объёма. Для тех, кто давно тренируется и любит железо.',
                    'pattern': 'Чередование: Лёгкие недели (Push/Pull ×2 + Legs/Glute + Metcon/Arms, 4 тренировки) и Тяжёлые недели (Push/Pull ×4 + Legs/Glute ×2, до 6 тренировок).',
                    'goal': 'масса',
                    'target_types': ['push', 'pull', 'legs', 'gluteLab', 'armBlast', 'metcon', 'bootcamp']
                })

        return patterns

    def _extract_athlete_patterns(self) -> List[Dict[str, Any]]:
        """Извлечь паттерны Athlete 1-5."""
        patterns = []

        # Athlete Level 1-5
        for level in range(1, 6):
            if level == 1:
                patterns.append({
                    'path': 'Athlete',
                    'level': 1,
                    'weeks': 4,
                    'frequency': '3-4',
                    'description': 'Подтянуть общую атлетичность: выносливость, скорость, работа сердца.',
                    'pattern': 'Metcon + Bootcamp - ядро. Upper/Push-Pull/Legs/Glute дают силовой фундамент как поддержка.',
                    'goal': 'здоровье',
                    'target_types': ['metcon', 'bootcamp', 'upperBody', 'push', 'pull', 'legs', 'gluteLab']
                })
            elif level == 2:
                patterns.append({
                    'path': 'Athlete',
                    'level': 2,
                    'weeks': 4,
                    'frequency': '4',
                    'description': 'Реально спортивный формат: много функционала + регулярный силовой сплит.',
                    'pattern': 'Metcon каждую неделю + Push/Pull + Legs/Glute + Upper/Full Body/Bootcamp для баланса.',
                    'goal': 'здоровье',
                    'target_types': ['metcon', 'bootcamp', 'push', 'pull', 'legs', 'gluteLab', 'upperBody', 'fullBody']
                })
            elif level == 3:
                patterns.append({
                    'path': 'Athlete',
                    'level': 3,
                    'weeks': 4,
                    'frequency': '4-5',
                    'description': 'Сбалансировать силу и функциональную выносливость.',
                    'pattern': 'Чередуются: Силовые недели (Push/Pull ×2 + Legs/Glute + Bootcamp) и Функциональные недели (Upper + Metcon ×2 + Legs/Glute + Bootcamp).',
                    'goal': 'здоровье',
                    'target_types': ['push', 'pull', 'legs', 'gluteLab', 'metcon', 'bootcamp', 'upperBody']
                })
            elif level == 4:
                patterns.append({
                    'path': 'Athlete',
                    'level': 4,
                    'weeks': 6,
                    'frequency': '4-5',
                    'description': 'Приблизить к режиму кроссфит-гонок/функциональных стартов. Подготовка атлета.',
                    'pattern': 'Много Metcon (до 2 раз в неделю) + Bootcamp + Legs/Glute в каждой неделе + Push/Pull и Upper укрепляют верх.',
                    'goal': 'здоровье',
                    'target_types': ['metcon', 'bootcamp', 'legs', 'gluteLab', 'push', 'pull', 'upperBody']
                })
            elif level == 5:
                patterns.append({
                    'path': 'Athlete',
                    'level': 5,
                    'weeks': 8,
                    'frequency': '4-6',
                    'description': 'Максимальный уровень атлетичности: высокая частота Metcon, регулярные ноги, силовой верх.',
                    'pattern': 'Metcon - сердце программы (2-3 раза в неделю). Legs/Glute в каждой неделе. Upper/Push-Pull - силовая поддержка верха.',
                    'goal': 'здоровье',
                    'target_types': ['metcon', 'bootcamp', 'legs', 'gluteLab', 'upperBody', 'push', 'pull']
                })

        return patterns

    def get_patterns_for_goal(self, goal: str, experience_level: str = None) -> List[Dict[str, Any]]:
        """
        Получить паттерны релевантные для цели пользователя.

        Args:
            goal: Цель пользователя (похудение, масса, рельеф, здоровье)
            experience_level: Уровень опыта (новичок, любитель, профи) - опционально

        Returns:
            Список релевантных паттернов
        """
        if not self.patterns:
            self.load_all_patterns()

        # Фильтр по цели
        relevant_patterns = [p for p in self.patterns if p['goal'] == goal]

        # Если указан уровень опыта - фильтруем по уровню
        if experience_level:
            if experience_level == 'новичок':
                relevant_patterns = [p for p in relevant_patterns if p['level'] <= 2]
            elif experience_level == 'любитель':
                relevant_patterns = [p for p in relevant_patterns if 2 <= p['level'] <= 4]
            elif experience_level == 'профи':
                relevant_patterns = [p for p in relevant_patterns if p['level'] >= 3]

        return relevant_patterns

    def get_example_patterns_for_prompt(
        self,
        goal: str,
        experience_level: str,
        max_examples: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Получить примеры паттернов для промпта LLM.

        Выбирает наиболее релевантные примеры на основе цели и опыта.

        Args:
            goal: Цель пользователя
            experience_level: Уровень опыта
            max_examples: Максимальное количество примеров

        Returns:
            Список примеров для промпта
        """
        relevant = self.get_patterns_for_goal(goal, experience_level)

        # Сортируем по уровню и берём разнообразные примеры
        if len(relevant) <= max_examples:
            return relevant

        # Берём равномерно распределённые примеры
        step = len(relevant) // max_examples
        return [relevant[i * step] for i in range(max_examples)]
