"""Test setup: use a fake in-memory database instead of a real MongoDB."""

import os
import mongomock
import pymongo

os.environ["MONGO_DBNAME"] = "tactile_test"
os.environ["SECRET_KEY"] = "test"
pymongo.MongoClient = mongomock.MongoClient
