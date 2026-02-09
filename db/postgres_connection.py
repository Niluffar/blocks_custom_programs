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
    def get_user_checkins(cls, user_id, limit=30):
        return cls.execute_query(
            """
            SELECT * FROM checkins
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    @classmethod
    def get_user_assessments(cls, user_id, limit=5):
        return cls.execute_query(
            """
            SELECT * FROM assessments
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    @classmethod
    def get_user_profile(cls, user_id):
        return cls.execute_one(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
