# from pymongo import MongoClient
# import os

# MONGO_HOST = os.getenv("MONGO_HOST")
# MONGO_PORT = int(os.getenv("MONGO_PORT"))
# MONGO_USER = os.getenv("MONGO_USER")
# MONGO_PASS = os.getenv("MONGO_PASSWORD")
# MONGO_DB   = os.getenv("MONGO_DATABASE_NAME")

# def get_mongo_collection(collection_name):
#     # 建立連線
#     client = MongoClient(
#         host=MONGO_HOST,
#         port=MONGO_PORT,
#         username=MONGO_USER,
#         password=MONGO_PASS,
#         authSource="admin"  # 如果是root帳號開在admin
#     )
#     db = client[MONGO_DB]
#     return db[collection_name]

# def insert_field(document):
#     collection = get_mongo_collection("field")
#     result = collection.insert_one(document)
#     return str(result.inserted_id)

# def find_fields(query=None):
#     collection = get_mongo_collection("field")
#     return list(collection.find(query or {}))
