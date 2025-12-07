import os
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users = db["users"]
user_agents = db["user_agents"]
appointments = db["appointments"]

oid = ObjectId("692f690369a23fcb22c1e68c")
user = users.find_one({"_id": oid, "email": "danielesilvestri2003@gmail.com"})
print(user)

print(f"Connected to MongoDB database: {MONGO_DB_NAME}")
