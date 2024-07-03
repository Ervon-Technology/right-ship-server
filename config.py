import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rys3tfuginmhoij'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://aniket:12345@cluster0.8sfpess.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'