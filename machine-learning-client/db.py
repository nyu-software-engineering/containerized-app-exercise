import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  

_client = None


def get_db():
    global _client  
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"])
        _client.admin.command("ping")  
    return _client[os.environ.get("MONGO_DBNAME", "myappdb")]
