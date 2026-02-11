"""
Загрузка данных пользователя из MongoDB и PostgreSQL
Вспомогательный модуль для получения всех необходимых данных для генерации плана
"""
from typing import Dict, List, Optional, Any
from db import MongoConnection, PostgresConnection


class UserDataLoader:
    """
    Загружает все необходимые данные пользователя для генерации плана тренировок.

    Объединяет данные из:
    - MongoDB: HeroPass, марафоны, блоки
    - PostgreSQL: InBody тесты, посещения, профиль
    """

    @staticmethod
    def load_all_data(user_id: str) -> Dict[str, Any]:
        """
        Загрузить все данные пользователя для генерации плана.

        Args:
            user_id: ID пользователя

        Returns:
            Dict с полными данными пользователя:
            {
                'user_profile': Dict,          # Профиль из PostgreSQL
                'questionnaire': Dict,         # Анкета из последнего блока
                'inbody_data': Dict,           # Последний InBody тест
                'checkins_data': List[Dict],   # История посещений (последние 90 дней)
                'marathons_data': List[Dict],  # История марафонов (последние 5)
                'heropass_data': Dict          # Активный HeroPass
            }
        """
        return {
            'user_profile': UserDataLoader.get_user_profile(user_id),
            'questionnaire': UserDataLoader.get_questionnaire(user_id),
            'inbody_data': UserDataLoader.get_latest_inbody(user_id),
            'checkins_data': UserDataLoader.get_checkins_history(user_id),
            'marathons_data': UserDataLoader.get_marathons_history(user_id),
            'heropass_data': UserDataLoader.get_heropass(user_id)
        }

    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        """
        Получить профиль пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя

        Returns:
            Dict с профилем или None
        """
        try:
            return PostgresConnection.get_user_profile(user_id)
        except Exception as e:
            import logging
            logging.warning(f"Ошибка при получении профиля пользователя {user_id}: {e}")
            return None

    @staticmethod
    def get_questionnaire(user_id: str) -> Optional[Dict]:
        """
        Получить анкету пользователя из последнего блока.

        Args:
            user_id: ID пользователя

        Returns:
            Dict с данными анкеты или None
        """
        try:
            # Получаем активный блок пользователя
            userblock = MongoConnection.get_active_user_block(user_id)

            if userblock and 'forms' in userblock:
                return userblock['forms']

            # Если нет активного блока, ищем последний созданный
            all_blocks = MongoConnection.get_user_blocks_by_user(user_id)
            if all_blocks:
                # Сортируем по дате создания (последний первый)
                all_blocks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                latest_block = all_blocks[0]

                if 'forms' in latest_block:
                    return latest_block['forms']

            return None

        except Exception as e:
            import logging
            logging.warning(f"Ошибка при получении анкеты пользователя {user_id}: {e}")
            return None

    @staticmethod
    def get_latest_inbody(user_id: str) -> Optional[Dict]:
        """
        Получить последний InBody тест пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)

        Returns:
            Dict с данными InBody теста или None
        """
        try:
            inbody = PostgresConnection.get_latest_inbody(user_id)

            if inbody:
                # Поля уже переименованы в запросе через AS
                return {
                    'body_fat_percentage': float(inbody['body_fat_percentage']) if inbody.get('body_fat_percentage') else None,
                    'muscle_mass': float(inbody['muscle_mass']) if inbody.get('muscle_mass') else None,
                    'fitness_score': float(inbody['fitness_score']) if inbody.get('fitness_score') else None,
                    'weight': float(inbody['weight']) if inbody.get('weight') else None,
                    'test_date': inbody.get('test_date')
                }

            return None

        except Exception as e:
            import logging
            logging.warning(f"Ошибка при получении InBody данных пользователя {user_id}: {e}")
            return None

    @staticmethod
    def get_checkins_history(user_id: str, days: int = 90) -> List[Dict]:
        """
        Получить историю посещений пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)
            days: Количество дней истории (по умолчанию 90 = ~3 месяца)

        Returns:
            List с данными посещений
        """
        try:
            # Получаем последние записи
            checkins = PostgresConnection.get_user_checkins(user_id, limit=days)

            # Фильтруем только за последние N дней
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            filtered_checkins = []
            for checkin in checkins:
                event_time = checkin.get('event_start_time')
                if event_time and event_time >= cutoff_date:
                    filtered_checkins.append({
                        'date': event_time,
                        'program_type': checkin.get('programset_type'),
                        'program_name': checkin.get('programset_name'),
                        'event_id': checkin.get('event_id')
                    })

            return filtered_checkins

        except Exception as e:
            import logging
            logging.warning(f"Ошибка при получении истории посещений пользователя {user_id}: {e}")
            return []

    @staticmethod
    def get_marathons_history(user_id: str, limit: int = 5) -> List[Dict]:
        """
        Получить историю марафонов пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)
            limit: Максимальное количество марафонов

        Returns:
            List с данными марафонов
        """
        try:
            marathons = PostgresConnection.get_user_marathons(user_id, limit=limit)

            # Конвертируем в удобный формат
            result = []
            for marathon in marathons:
                # Рассчитываем процент посещаемости
                total = marathon.get('total_visits_for_marathon', 0)
                user_visits = marathon.get('user_visits_for_marathon', 0)
                attendance_rate = (user_visits / total) if total > 0 else 0

                # Определяем статус (завершён если дата окончания прошла)
                from datetime import datetime
                end_time = marathon.get('marathon_endtime_utc')
                is_completed = end_time and end_time < datetime.now()

                result.append({
                    'marathon_id': marathon.get('marathon_id'),
                    'name': marathon.get('marathon_name'),
                    'start_date': marathon.get('marathon_starttime_utc'),
                    'end_date': marathon.get('marathon_endtime_utc'),
                    'total_visits': total,
                    'user_visits': user_visits,
                    'attendance_rate': attendance_rate,
                    'status': 'completed' if is_completed else 'inProgress',
                    'payment_type': marathon.get('payment_type'),
                    'is_trial': marathon.get('is_trial', False)
                })

            return result

        except Exception as e:
            import logging
            logging.warning(f"Ошибка при получении истории марафонов пользователя {user_id}: {e}")
            return []

    @staticmethod
    def get_heropass(user_id: str) -> Optional[Dict]:
        """
        Получить активный HeroPass пользователя.

        Сначала пытается получить из PostgreSQL view,
        если не получается - fallback на MongoDB.
        pilatesVisits всегда берётся из MongoDB (там это поле хранится).

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)

        Returns:
            Dict с данными HeroPass или None.
            Включает pilatesVisits (лимит Reshape на весь абонемент) если поле есть в MongoDB.
        """
        import logging

        try:
            # Всегда запрашиваем MongoDB для pilatesVisits
            heropass_mongo = MongoConnection.get_active_heropass(user_id)
            pilates_visits = heropass_mongo.get('pilatesVisits') if heropass_mongo else None

            # Пытаемся получить основные данные из PostgreSQL view
            heropass_pg = PostgresConnection.get_user_heropass(user_id)

            if heropass_pg:
                return {
                    'club_id': heropass_pg.get('heropass_club_id'),
                    'club_name': heropass_pg.get('heropass_club_name'),
                    'status': 'active',
                    'start_time': heropass_pg.get('heropass_starttime_utc'),
                    'end_time': heropass_pg.get('heropass_endtime_utc'),
                    'pilatesVisits': pilates_visits
                }

            # Fallback на MongoDB если нет в PostgreSQL
            logging.info(f"HeroPass не найден в PostgreSQL для пользователя {user_id}, пробуем MongoDB")

            if heropass_mongo:
                club_info = MongoConnection.get_user_club_info(user_id)

                if club_info:
                    return {
                        'club_id': str(club_info['club_id']),
                        'club_name': club_info['club_name'],
                        'status': heropass_mongo.get('status', 'active'),
                        'start_time': heropass_mongo.get('startTime'),
                        'end_time': heropass_mongo.get('endTime'),
                        'pilatesVisits': pilates_visits
                    }

                return {
                    'status': heropass_mongo.get('status', 'active'),
                    'club_id': str(heropass_mongo.get('club')) if 'club' in heropass_mongo else None,
                    'pilatesVisits': pilates_visits
                }

            return None

        except Exception as e:
            logging.warning(f"Ошибка при получении HeroPass пользователя {user_id}: {e}")
            return None
