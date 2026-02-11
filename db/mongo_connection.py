import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class MongoConnection:
    _client = None
    _db = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            uri = os.getenv("MONGO_CONNECTION_STRING", "mongodb://localhost:27017")
            cls._client = MongoClient(uri)
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._db is None:
            db_name = os.getenv("MONGO_DB", "hero-app-prod")
            cls._db = cls.get_client()[db_name]
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

    # --- Коллекции ---

    @classmethod
    def blocks(cls):
        return cls.get_db()["blocks"]

    @classmethod
    def user_blocks(cls):
        return cls.get_db()["userblocks"]

    @classmethod
    def users(cls):
        return cls.get_db()["users"]

    @classmethod
    def user_heropasses(cls):
        return cls.get_db()["userheropasses"]

    @classmethod
    def programsets(cls):
        return cls.get_db()["programsets"]

    @classmethod
    def user_marathons(cls):
        return cls.get_db()["usermarathons"]

    @classmethod
    def programsets(cls):
        return cls.get_db()["programsets"]

    # --- Запросы для блоков ---

    @classmethod
    def get_block_by_id(cls, block_id):
        from bson import ObjectId
        return cls.blocks().find_one({"_id": ObjectId(block_id)})

    @classmethod
    def get_user_block(cls, user_block_id):
        from bson import ObjectId
        return cls.user_blocks().find_one({"_id": ObjectId(user_block_id)})

    @classmethod
    def get_user_blocks_by_user(cls, user_id):
        from bson import ObjectId
        return list(cls.user_blocks().find({"user": ObjectId(user_id)}))

    @classmethod
    def get_active_user_block(cls, user_id):
        from bson import ObjectId
        return cls.user_blocks().find_one({
            "user": ObjectId(user_id),
            "status": "active"
        })

    @classmethod
    def update_user_block(cls, user_block_id, update_data):
        from bson import ObjectId
        return cls.user_blocks().update_one(
            {"_id": ObjectId(user_block_id)},
            {"$set": update_data}
        )

    # --- Запросы для HeroPass ---

    @classmethod
    def get_active_heropass(cls, user_id):
        """
        Получить активный HeroPass пользователя.

        Args:
            user_id: ID пользователя (str или ObjectId)

        Returns:
            Dict с данными HeroPass или None
        """
        from bson import ObjectId

        # Конвертируем user_id в ObjectId если это строка
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return cls.user_heropasses().find_one({
            "user": user_id,
            "status": "active"
        })

    @classmethod
    def get_heropass_by_id(cls, heropass_id):
        """
        Получить HeroPass по его ID.

        Args:
            heropass_id: ID HeroPass (str или ObjectId)

        Returns:
            Dict с данными HeroPass или None
        """
        from bson import ObjectId

        if isinstance(heropass_id, str):
            heropass_id = ObjectId(heropass_id)

        return cls.user_heropasses().find_one({"_id": heropass_id})

    @classmethod
    def get_user_heropasses(cls, user_id):
        """
        Получить все HeroPass пользователя.

        Args:
            user_id: ID пользователя (str или ObjectId)

        Returns:
            List документов HeroPass
        """
        from bson import ObjectId

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return list(cls.user_heropasses().find({"user": user_id}))

    # --- Запросы для марафонов ---

    @classmethod
    def get_user_marathons(cls, user_id, limit=5):
        """
        Получить историю марафонов пользователя.

        Args:
            user_id: ID пользователя (str или ObjectId)
            limit: Максимальное количество марафонов

        Returns:
            List документов марафонов (отсортированы по дате создания)
        """
        from bson import ObjectId

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return list(cls.user_marathons().find({
            "user": user_id
        }).sort("created_at", -1).limit(limit))

    @classmethod
    def get_completed_marathons(cls, user_id):
        """
        Получить только завершённые марафоны пользователя.

        Args:
            user_id: ID пользователя (str или ObjectId)

        Returns:
            List завершённых марафонов
        """
        from bson import ObjectId

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return list(cls.user_marathons().find({
            "user": user_id,
            "status": "completed"
        }).sort("created_at", -1))

    # --- Запросы для programsets ---

    @classmethod
    def get_all_program_types(cls):
        """
        Получить все уникальные типы программ из programsets.

        Returns:
            List уникальных типов программ
        """
        return cls.programsets().distinct("type")

    @classmethod
    def get_programsets_by_type(cls, program_type):
        """
        Получить все programsets определённого типа.

        Args:
            program_type: Тип программы (например, 'bootcamp')

        Returns:
            List документов programsets
        """
        return list(cls.programsets().find({"type": program_type}))

    # --- Вспомогательные методы ---

    @classmethod
    def get_user_club_info(cls, user_id):
        """
        Получить информацию о клубе пользователя через активный HeroPass.

        Args:
            user_id: ID пользователя (str или ObjectId)

        Returns:
            Dict с информацией о клубе:
            - club_id: ObjectId клуба
            - club_name: Название клуба
            или None если HeroPass не найден или клуб не найден
        """
        from bson import ObjectId

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Получаем активный HeroPass
        heropass = cls.get_active_heropass(user_id)

        if not heropass or 'club' not in heropass:
            return None

        club_id = heropass['club']

        # Получаем информацию о клубе
        club_doc = cls.get_db()['clubs'].find_one({'_id': club_id})

        if not club_doc:
            return None

        return {
            'club_id': club_id,
            'club_name': club_doc.get('name')
        }

    # --- Запросы для programsets ---

    @classmethod
    def get_available_program_types_for_club(cls, club_id):
        """
        Получить список доступных типов программ для конкретного клуба.

        Запрашивает реальные programsets из MongoDB и возвращает уникальные типы.

        Args:
            club_id: ID клуба (ObjectId или str)

        Returns:
            List[str]: Список уникальных типов программ доступных в этом клубе
        """
        from bson import ObjectId

        if isinstance(club_id, str):
            club_id = ObjectId(club_id)

        # Получаем все programsets для этого клуба
        program_types = cls.programsets().distinct('type', {'club': club_id})

        return list(program_types)

    @classmethod
    def get_all_program_types(cls):
        """
        Получить список всех возможных типов программ в системе.

        Returns:
            List[str]: Список всех уникальных типов программ
        """
        return list(cls.programsets().distinct('type'))
