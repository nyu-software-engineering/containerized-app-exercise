"""Adds some sample sounds to the database so the home page has something to show.

Run it with: python seed.py <your username>
"""

import os
import sys
import pymongo
from dotenv import load_dotenv

load_dotenv()

connection = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = connection[os.getenv("MONGO_DBNAME")]

username = sys.argv[1].lower()
user = db.users.find_one({"username": username})

if user is None:
    print("that user doesn't exist, sign up first")
    sys.exit()

sounds = [
    {"name": "Glass tap", "material": "glass", "note": "A5", "instrument": "bell"},
    {"name": "Desk knock", "material": "wood", "note": "C3", "instrument": "drum"},
    {"name": "Keys jingle", "material": "metal", "note": "F6", "instrument": "shaker"},
    {"name": "Paper crumple", "material": "paper", "note": "D4", "instrument": "snare"},
    {"name": "Pot lid hum", "material": "metal", "note": "G2", "instrument": "pad"},
]

for sound in sounds:
    db.sounds.insert_one(
        {
            "user_id": str(user["_id"]),
            "name": sound["name"],
            "material": sound["material"],
            "analysis": {"note": sound["note"], "tags": []},
            "instrument": {"type": sound["instrument"]},
        }
    )

print("added", len(sounds), "sounds for", username)
