import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class PostgresConnection:
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._conn is None or cls._conn.closed:
            cls._conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                dbname=os.getenv("POSTGRES_DB", "hj_database"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "password"),
            )
        return cls._conn

    @classmethod
    def close(cls):
        if cls._conn and not cls._conn.closed:
            cls._conn.close()
            cls._conn = None

    @classmethod
    def execute_query(cls, query, params=None):
        conn = cls.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    @classmethod
    def execute_one(cls, query, params=None):
        conn = cls.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    # --- Запросы для атлетов ---

    @classmethod
    def get_user_checkins(cls, user_id, limit=90):
        """
        Получить историю посещений пользователя.

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)
            limit: Количество записей

        Returns:
            List с данными посещений
        """
        return cls.execute_query(
            """
            SELECT
                uch."user" as user_id,
                uch.id as checkin_id,
                e.id as event_id,
                e.starttime as event_start_time,
                p.name as programset_name,
                p.type as programset_type
            FROM
                raw.usercheckin uch
            LEFT JOIN
                raw.event e
                ON uch."event" = e.id
            LEFT JOIN
                raw.programset p
                ON e.programset = p.id
            WHERE uch."user" = %s
            ORDER BY e.starttime DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    @classmethod
    def get_user_strength_measurements(cls, user_id, limit=10):
        """
        Получить результаты 1RepMax тестов пользователя.

        Args:
            user_id: ID пользователя
            limit: Количество записей

        Returns:
            List с результатами assessment
        """
        return cls.execute_query(
            """
            SELECT
                user_id,
                exercise_id,
                event_id,
                measurement_type,
                weight,
                reps,
                one_rep_max,
                created_at_utc
            FROM
                ris.v_user_strength_measurements
            WHERE user_id = %s
            ORDER BY created_at_utc DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    @classmethod
    def get_user_profile(cls, user_id):
        """
        Получить профиль пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Dict с данными профиля
        """
        return cls.execute_one(
            """
            SELECT
                user_id,
                nickname,
                gender,
                age
            FROM
                ris.core_user
            WHERE user_id = %s
            """,
            (user_id,)
        )

    @classmethod
    def get_latest_inbody(cls, user_id):
        """
        Получить последний InBody тест пользователя.

        Args:
            user_id: ID пользователя (MongoDB ObjectId в виде строки)

        Returns:
            Dict с данными InBody теста или None
        """
        return cls.execute_one(
            """
            SELECT
                user_id,
                test_date,
                pbf as body_fat_percentage,
                smm as muscle_mass,
                fs as fitness_score,
                wt as weight
            FROM
                ris.v_user_inbody_tests
            WHERE user_id = %s
            ORDER BY test_date DESC
            LIMIT 1
            """,
            (user_id,)
        )

    @classmethod
    def get_user_inbody_history(cls, user_id, limit=5):
        """
        Получить историю InBody тестов пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество тестов

        Returns:
            List с InBody тестами
        """
        return cls.execute_query(
            """
            SELECT
                user_id,
                test_date,
                pbf as body_fat_percentage,
                smm as muscle_mass,
                fs as fitness_score,
                wt as weight
            FROM
                ris.v_user_inbody_tests
            WHERE user_id = %s
            ORDER BY test_date DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    @classmethod
    def get_user_heropass(cls, user_id):
        """
        Получить активный HeroPass пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя

        Returns:
            Dict с данными HeroPass или None
        """
        return cls.execute_one(
            """
            SELECT
                user_id,
                userheropass_id,
                heropass_starttime_utc,
                heropass_endtime_utc,
                is_heropass_active,
                heropass_club_id,
                heropass_club_name
            FROM
                ris.v_user_heropass
            WHERE user_id = %s AND is_heropass_active = true
            ORDER BY heropass_starttime_utc DESC
            LIMIT 1
            """,
            (user_id,)
        )

    @classmethod
    def get_user_marathons(cls, user_id, limit=5):
        """
        Получить историю марафонов пользователя из PostgreSQL.

        Args:
            user_id: ID пользователя
            limit: Количество марафонов

        Returns:
            List с данными марафонов
        """
        return cls.execute_query(
            """
            SELECT
                user_id,
                usermarathonevent_id,
                marathon_id,
                marathon_name,
                total_visits_for_marathon,
                user_visits_for_marathon,
                marathon_starttime_utc,
                marathon_endtime_utc,
                payment_type,
                is_trial
            FROM
                ris.v_user_marathons
            WHERE user_id = %s
            ORDER BY marathon_starttime_utc DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
