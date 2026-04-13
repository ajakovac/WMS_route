from pymongo import MongoClient

def get_db():
    YOUR_PASSWORD = "ogxEn9jDngKqCHXr"
    MONGO_URI = f"mongodb+srv://wms_route:{YOUR_PASSWORD}@devcluster1.39ltss0.mongodb.net/?appName=devcluster1"
    client = MongoClient(MONGO_URI)

    # select database
    db = client["test"]
    return db
