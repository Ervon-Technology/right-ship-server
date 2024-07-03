from pymongo import MongoClient
import certifi
ca = certifi.where()
class MongoDB:
    def __init__(self, uri):
        self.client = MongoClient(uri,tlsCAFile=ca)
        self.db = self.client.right_ship  # Replace with your database name

    def get_collection(self, collection_name):
        return self.db[collection_name]


mongo_db = MongoDB("mongodb+srv://aniket:12345@cluster0.8sfpess.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
