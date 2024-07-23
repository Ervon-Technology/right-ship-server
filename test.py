
from db import mongo_db
from flask import jsonify
from datetime import datetime
from datetime import timezone
from bson.objectid import ObjectId
from bson import ObjectId, json_util

def checkPhoneNumberExists(mobile_no):
    try:
    
        user_type_to_collection = {
            "employee": "employee",
            "company": "company_team",
            "admin": "team"
        }
        for user_type, collection_name in user_type_to_collection.items():
            user_data = mongo_db.get_collection(collection_name).find_one({"mobile_no": mobile_no}, {"_id": 0})
            if user_data:
             
               
                return  ({"code": 409, "msg": f"This mobile number already exists as {user_type}"})

        return ({"code": 200, "msg": "User not found"})

    except Exception as e:
        return ({"code": 500, "msg": "Error: " + str(e)})
    
# checkPhoneNumberExists('6206630515')