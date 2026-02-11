"""
Фильтрация типов программ по доступным зонам клуба
Использует данные HeroPass пользователя и маппинг зон из club_zones.py
"""
import math
from typing import Dict, List, Optional
from rules.club_zones import (
    PROGRAM_TYPE_TO_ZONES,
    CLUB_STRUCTURE,
    get_club_zones,
    get_club_capacities,
    get_club_load_factors,
    rank_program_types_by_availability
)
from rules.recovery_rules import RECOVERY_RULES

# Длительность одного блока в днях (8 недель = 56 дней)
BLOCK_DURATION_DAYS = 56


class ClubFilter:
    """
    Фильтрует типы программ по доступным зонам клуба пользователя.

    Использует:
    - HeroPass пользователя для определения клуба
    - Структуру клуба из club_zones.py
    - Load factors и capacities для ранжирования альтернатив
    """

    def get_user_club_data(self, user_id: str, heropass_data: Optional[Dict] = None) -> Dict:
        """
        Получить данные клуба пользователя из активного HeroPass.

        Args:
            user_id: ID пользователя
            heropass_data: Данные HeroPass (опционально, из data_loader или для тестирования)

        Returns:
            Dict с данными клуба:
            - club_id: ID клуба
            - club_name: Название клуба
            - available_program_types: Список доступных типов программ (из programsets)
            - zones: Список доступных зон
            - capacities: Вместимость зон
            - load_factors: Load factors зон
            - reshape_per_block: Лимит Reshape на один блок

        Raises:
            ValueError: Если у пользователя нет активного HeroPass
            Exception: Если произошла ошибка при получении данных из БД
        """
        # Если данные переданы напрямую (из data_loader или для тестирования)
        if heropass_data:
            club_name = heropass_data.get('club_name')
            club_id = heropass_data.get('club_id')  # Может быть None

            if club_name and club_name in CLUB_STRUCTURE:
                data = self._build_club_data(club_name, club_id)
                data['reshape_per_block'] = self._calculate_reshape_per_block(heropass_data)
                return data

        # Запрос к MongoDB для получения клуба пользователя
        import logging
        from db import MongoConnection
        from bson import ObjectId

        heropass = None
        try:
            # Получаем активный HeroPass (полный документ — нужен pilatesVisits)
            heropass = MongoConnection.get_active_heropass(user_id)
        except Exception as e:
            # Ошибка подключения к MongoDB (authentication, network, и т.д.)
            # Логируем предупреждение, но НЕ падаем
            logging.warning(
                f"Не удалось подключиться к MongoDB для получения HeroPass пользователя {user_id}: {e}"
            )

        # Если HeroPass не найден (либо из-за ошибки подключения, либо его просто нет)
        if not heropass:
            raise ValueError(
                f"У пользователя {user_id} нет активного HeroPass. "
                f"Генерация плана тренировок невозможна без активного абонемента."
            )

        # HeroPass найден - получаем данные клуба
        try:
            club_info = MongoConnection.get_user_club_info(user_id)
            club_id = heropass.get('club')  # ObjectId клуба

            if not club_id or not club_info:
                raise ValueError(
                    f"У пользователя {user_id} некорректный HeroPass (нет данных о клубе). "
                    f"Проверьте поле 'club' в HeroPass."
                )

            club_name = club_info.get('club_name')

            # Получаем РЕАЛЬНЫЕ доступные типы программ из programsets
            available_types = MongoConnection.get_available_program_types_for_club(club_id)

            # Получаем данные о зонах из CLUB_STRUCTURE (для capacities/load_factors)
            club_structure = CLUB_STRUCTURE.get(club_name, {})

            return {
                'club_id': str(club_id),
                'club_name': club_name,
                'available_program_types': available_types,  # Реальные programsets
                'zones': club_structure.get('zones', []),    # Зоны для справки
                'capacities': club_structure.get('capacities', {}),
                'load_factors': club_structure.get('load_factors', {}),
                'reshape_per_block': self._calculate_reshape_per_block({
                    'pilatesVisits': heropass.get('pilatesVisits'),
                    'start_time': heropass.get('startTime'),
                    'end_time': heropass.get('endTime'),
                })
            }

        except ValueError:
            # ValueError пробрасываем дальше (это логическая ошибка, не проблема БД)
            raise
        except Exception as e:
            # Другие ошибки (проблемы с БД при получении club_info или programsets)
            logging.error(f"Ошибка при получении данных клуба для пользователя {user_id}: {e}")
            raise Exception(
                f"Не удалось получить данные клуба для пользователя {user_id}. "
                f"Проверьте подключение к базе данных и корректность данных HeroPass."
            ) from e

    def _calculate_reshape_per_block(self, heropass_data: Dict) -> int:
        """
        Рассчитать лимит Reshape на один блок (8 недель).

        pilatesVisits — лимит на весь абонемент.
        Если поля нет — значит reshape недоступен (0).
        Распределяем равномерно по блокам в абонементе.

        Args:
            heropass_data: Данные HeroPass с pilatesVisits и датами

        Returns:
            int: количество Reshape тренировок на один блок (0 если недоступен)
        """
        pilates_visits = heropass_data.get('pilatesVisits')

        # Нет поля = нет доступа к reshape
        if pilates_visits is None or pilates_visits <= 0:
            return 0

        # Определяем количество блоков в абонементе по датам
        start_time = heropass_data.get('start_time')
        end_time = heropass_data.get('end_time')

        if start_time and end_time:
            try:
                from datetime import datetime

                # Приводим к datetime если это строка
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                total_days = (end_time - start_time).days
                if total_days > 0:
                    blocks_in_subscription = max(1, total_days / BLOCK_DURATION_DAYS)
                    return math.ceil(pilates_visits / blocks_in_subscription)
            except (ValueError, TypeError):
                pass

        # Если даты не удалось определить — делим на 6 месяцев (3 блока) по умолчанию
        return math.ceil(pilates_visits / 3)

    def _build_club_data(self, club_name: str, club_id: Optional[str] = None) -> Dict:
        """
        Построить данные клуба из CLUB_STRUCTURE и MongoDB.

        Args:
            club_name: Название клуба
            club_id: ID клуба (опционально). Если есть, запросим programsets из MongoDB.

        Returns:
            Dict с данными клуба включая available_program_types
        """
        club_info = CLUB_STRUCTURE.get(club_name, {})

        # Попытка получить реальные programsets из MongoDB
        available_program_types = []
        if club_id:
            try:
                from db import MongoConnection
                available_program_types = MongoConnection.get_available_program_types_for_club(club_id)
            except Exception as e:
                import logging
                logging.warning(f"Не удалось загрузить programsets для клуба {club_name}: {e}")

        # Если не удалось получить из MongoDB, используем zone-based filtering как fallback
        if not available_program_types:
            import logging
            logging.info(f"Используется zone-based filtering для клуба {club_name}")
            zones = club_info.get('zones', [])
            all_program_types = list(RECOVERY_RULES.keys())
            available_program_types = self.filter_available_program_types(all_program_types, zones)

        return {
            'club_id': club_id or club_name,
            'club_name': club_name,
            'available_program_types': available_program_types,
            'zones': club_info.get('zones', []),
            'capacities': club_info.get('capacities', {}),
            'load_factors': club_info.get('load_factors', {})
        }

    def _get_all_zones(self) -> List[str]:
        """Получить список всех возможных зон."""
        all_zones = set()
        for club_data in CLUB_STRUCTURE.values():
            all_zones.update(club_data.get('zones', []))
        return list(all_zones)

    def filter_available_program_types(
        self,
        all_program_types: List[str],
        club_zones: List[str]
    ) -> List[str]:
        """
        Фильтровать типы программ по доступным зонам клуба.

        Args:
            all_program_types: Список всех типов программ
            club_zones: Список доступных зон в клубе

        Returns:
            Список доступных типов программ
        """
        available_types = []

        for ptype in all_program_types:
            # Получить требуемые зоны для этого типа программы
            required_zones = PROGRAM_TYPE_TO_ZONES.get(ptype, [])

            # Если зоны не требуются (education) - программа доступна везде
            if not required_zones:
                available_types.append(ptype)
                continue

            # Программа доступна если хотя бы одна из требуемых зон есть в клубе
            if any(zone in club_zones for zone in required_zones):
                available_types.append(ptype)

        return available_types

    def rank_alternatives_by_capacity(
        self,
        program_types: List[str],
        club_name: str
    ) -> Dict[str, float]:
        """
        Ранжировать альтернативные типы программ по доступности зон.

        Учитывает load factor и capacity зон.
        Более высокий score = менее загруженная зона = приоритетнее для альтернативы.

        Args:
            program_types: Список типов программ для ранжирования
            club_name: Название клуба

        Returns:
            Dict {тип_программы: availability_score}
        """
        if not club_name or club_name not in CLUB_STRUCTURE:
            # Если клуб неизвестен - все типы равноприоритетны
            return {ptype: 1.0 for ptype in program_types}

        # Используем функцию из club_zones.py
        return rank_program_types_by_availability(program_types, club_name)

    def get_best_alternatives(
        self,
        main_type: str,
        all_available_types: List[str],
        club_name: str,
        count: int = 2
    ) -> List[str]:
        """
        Получить лучшие альтернативные типы программ для основного типа.

        Используется при генерации recommendedPlan для добавления 1-2 альтернатив
        на случай занятости основного типа.

        Args:
            main_type: Основной тип программы
            all_available_types: Все доступные типы в клубе
            club_name: Название клуба
            count: Количество альтернатив (по умолчанию 2)

        Returns:
            Список альтернативных типов (отсортированные по приоритету)
        """
        # Убрать основной тип из списка
        candidates = [t for t in all_available_types if t != main_type]

        if not candidates:
            return []

        # Ранжировать кандидатов по доступности
        rankings = self.rank_alternatives_by_capacity(candidates, club_name)

        # Отсортировать по score (descending) и взять топ N
        sorted_alternatives = sorted(
            rankings.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [alt[0] for alt in sorted_alternatives[:count]]

    def filter_program_weights_by_club(
        self,
        program_weights: Dict[str, float],
        club_zones: List[str]
    ) -> Dict[str, float]:
        """
        Фильтровать веса программ по доступным зонам и перенормализовать.

        Используется для фильтрации goal_mappings по клубу.

        Args:
            program_weights: Словарь {тип_программы: вес}
            club_zones: Список доступных зон

        Returns:
            Отфильтрованные и перенормализованные веса
        """
        # Фильтрация
        filtered_weights = {}

        for ptype, weight in program_weights.items():
            required_zones = PROGRAM_TYPE_TO_ZONES.get(ptype, [])

            # Если зоны не требуются или хотя бы одна зона доступна
            if not required_zones or any(zone in club_zones for zone in required_zones):
                filtered_weights[ptype] = weight

        # Перенормализация весов
        if filtered_weights:
            total = sum(filtered_weights.values())
            if total > 0:
                filtered_weights = {k: v/total for k, v in filtered_weights.items()}

        return filtered_weights
