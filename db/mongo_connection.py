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

    # --- Запросы ---

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
