from db import mongo_db
from flask import jsonify
from datetime import datetime
from datetime import timezone, timedelta
from bson.objectid import ObjectId
from bson import ObjectId, json_util

import os

def routes(payload,function):
    if function.lower() == 'register':
        
        mobile_no = payload.get('mobile_no', '')
        if not mobile_no:
            return {"code": 400, "error": "mobile_no key not defined"}
        
        phone_number = str(mobile_no)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Check if the OTP session is verified
        session = mongo_db.get_collection('otp_sessions').find_one({"mobile_no": phone_number, "verified": True}, sort=[("created_date", -1)])
        if not session or session['created_date'].replace(tzinfo=timezone.utc) < (datetime.now(timezone.utc) - timedelta(minutes=5)):
            return {"code": 400, "error": "OTP not verified or expired"}
        
        employeeData = {
            "status": "active",
            "mobile_no": mobile_no,
            "joined_date": datetime.now(timezone.utc).strftime('%d %b, %Y'),
            "created_date": datetime.now(timezone.utc)
        }
        # Check if the user already exists
        check_if_exists = mongo_db.get_collection('employee').find_one({"mobile_no": mobile_no})
        if check_if_exists is None:
            result = mongo_db.get_collection('employee').insert_one(employeeData)
            employeeData['_id'] = str(result.inserted_id)
            return jsonify({"code": 200, "msg": "Employee created successfully", "employee": employeeData})
        else:
            if '_id' in list(check_if_exists):
                check_if_exists['_id'] = str(check_if_exists['_id'])
            return {"code": 400, "msg": f" ({phone_number}) Already registered ", "data": check_if_exists}

    if function.lower() == 'login':
        
        mobile_no = payload.get('mobile_no', '')
        if not mobile_no:
            return {"code": 400, "error": "mobile_no key not defined"}
        
        phone_number = str(mobile_no)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Check if the OTP session is verified
        session = mongo_db.get_collection('otp_sessions').find_one({"mobile_no": phone_number, "verified": True}, sort=[("created_date", -1)])
       
        if not session or session['created_date'].replace(tzinfo=timezone.utc) < (datetime.now(timezone.utc) - timedelta(minutes=5)):
            return {"code": 400, "error": "OTP not verified or expired"}
           
        
        # Check if the user already exists
        check_if_exists = mongo_db.get_collection('employee').find_one({"mobile_no": mobile_no})
        if check_if_exists is None:
            return jsonify({"code": 500, "msg": "Number not registered"})
        else:
            check_if_exists['_id'] = str(check_if_exists['_id'])
            return {"code": 200, "msg": f" ({phone_number}) login successful ", "data": check_if_exists}

    if function.lower() == 'update':
       
        employee_id = payload.get('employee_id', '')

        if not employee_id:
            return jsonify({"code": 400, "msg": "employee_id is required"}), 400

        # Prepare the data to be updated
        update_data = {key: value for key, value in data.items() if key != 'employee_id'}
        update_data["updated_date"] = datetime.now(timezone.utc)

        # Update the existing document
        result = mongo_db.get_collection('employee').update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            return jsonify({"code": 200, "msg": "Employee data updated successfully"}), 200
        else:
            return jsonify({"code": 202, "msg": "No data found for updates"}), 202
   
    else:
        return jsonify({"error": "Invalid function"}), 400
