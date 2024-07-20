
from db import mongo_db
from flask import jsonify
from datetime import datetime
from datetime import timezone
from bson.objectid import ObjectId
from bson import ObjectId, json_util

import os

def routes(payload, function):
    if function.lower() == 'create':
        user_id = payload.get('user_id')
        company_id = payload.get('company_id')
        name = payload.get('name')
        email = payload.get('email')
        issue = payload.get('issue')
        status = payload.get('status')
        
        if not user_id or not name or not email or not issue or not status or not company_id:
            return jsonify({"error": "company_id, user_id, name, email, status, and issue keys are required"}), 400
        
        payload['created_date'] = datetime.utcnow()
        
        try:
            # Check if the same issue already exists
            existing_issue = mongo_db.get_collection('support').find_one({
                "user_id": user_id,
                "issue": issue,
                "status": status
            })
            
            if existing_issue:
                return jsonify({"code":400,"message": "The same issue already exists. Please change the issue and try again"}), 409
            
            mongo_db.get_collection('support').insert_one(payload)
            del payload['_id']
            return jsonify({"code":200,"message": "Issue created successfully", "issue": payload}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    if function.lower() == 'get':
        try:
            # Use the payload to search for issues
            search_query = payload
            results = list(mongo_db.get_collection('support').find(search_query))
            for result in results:
                result['_id'] = str(result['_id'])  # Convert ObjectId to string for JSON serialization
                result['support_id'] = str(result['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify({"code": 200, "issues": results}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif function.lower() == 'update':
        issue_id = payload.get('support_id')
        if not issue_id:
            return jsonify({"error": "support_id key is required"}), 400

        update_data = {key: value for key, value in payload.items() if key != 'support_id'}
        update_data["updated_date"] = datetime.utcnow()

        try:
            result = mongo_db.get_collection('support').update_one(
                {"_id": ObjectId(issue_id)},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return jsonify({"code": 200, "message": "Issue updated successfully"}), 200
            else:
                return jsonify({"code": 202, "message": "No data found for updates"}), 202
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif function.lower() == 'delete':
        issue_id = payload.get('support_id')
        if not issue_id:
            return jsonify({"error": "support_id key is required"}), 400

        try:
            result = mongo_db.get_collection('support').delete_one({"_id": ObjectId(issue_id)})
            if result.deleted_count > 0:
                return jsonify({"code": 200, "message": "Issue deleted successfully"}), 200
            else:
                return jsonify({"code": 202, "message": "No data found for deletion"}), 202
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid function"}), 400
    
    