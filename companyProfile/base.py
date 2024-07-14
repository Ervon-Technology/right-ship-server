from db import mongo_db
from flask import jsonify
from datetime import datetime
from bson.objectid import ObjectId
from bson import ObjectId, json_util


def routes(payload, function):
    if function.lower() == 'details':
        company_id = payload.get('company_id', '')

        # Add or update company data
        if company_id:
            payload["_id"] = ObjectId(company_id)
        
        payload["updated_date"] = datetime.utcnow()
        
        # Use upsert to either update the existing document or insert a new one
        result = mongo_db.get_collection('companies').update_one(
            {"_id": ObjectId(company_id)} if company_id else {"company_email": payload.get('company_email'), "company_url": payload.get('company_url')},
            {"$set": payload},
            upsert=True
        )
        
        if result.upserted_id:
            company_id = str(result.upserted_id)
            return jsonify({"code": 201, "msg": "Company data created successfully", "company_id": company_id}), 201
        elif result.modified_count > 0:
            return jsonify({"code": 200, "msg": "Company data updated successfully"}), 200
        else:
            return jsonify({"code": 202, "msg": "No data found for updates"}), 202

    elif function.lower() == 'get':
        try:
            if 'company_id' in payload:
                payload['_id'] = ObjectId(payload['company_id'])
                del payload['company_id']

            result = list(mongo_db.get_collection('companies').find(payload))
            for company in result:
                company['company_id'] = str(company['_id'])
                company['_id'] = str(company['_id'])
            
            return jsonify({"code": 200, "data": result, "msg": "Successfully fetched company data"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function.lower() == 'delete_keys':
        try:
            company_id = payload.get('company_id')
            keys_to_delete = payload.get('keys_to_delete', [])

            if not company_id or not keys_to_delete:
                return jsonify({"error": "company_id and keys_to_delete are required"}), 400
            
            unset_fields = {key: "" for key in keys_to_delete}

            result = mongo_db.get_collection('companies').update_one(
                {"_id": ObjectId(company_id)},
                {"$unset": unset_fields}
            )

            if result.modified_count == 0:
                return jsonify({"code": 202, "msg": "No keys found for deletion"}), 202
            else:
                return jsonify({"code": 200, "msg": "Keys deleted successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function.lower() == 'register':
        try:
            mobile_no = payload.get('mobile_no')
            otp = payload.get('otp')  # Assume OTP is already verified elsewhere
            company_data = payload
            
            if not mobile_no or not otp:
                return jsonify({"error": "Mobile number and OTP are required"}), 400
            
            # Create or find company admin based on mobile number
            admin_data = {
                "mobile_no": mobile_no,
                "created_date": datetime.utcnow()
            }
            admin_result = mongo_db.get_collection('company_admins').find_one_and_update(
                {"mobile_no": mobile_no},
                {"$setOnInsert": admin_data},
                upsert=True,
                return_document=True
            )
            company_data['company_admin_id'] = str(admin_result['_id'])

            # Check if company with the same company_admin_id exists
            existing_company = mongo_db.get_collection('companies').find_one({"company_admin_id": company_data['company_admin_id']})
            if existing_company:
                # Update existing company data
                result = mongo_db.get_collection('companies').update_one(
                    {"company_admin_id": company_data['company_admin_id']},
                    {"$set": company_data}
                )
                if result.modified_count == 0:
                    return jsonify({"code": 202, "msg": "No data found for updates"}), 202
                else:
                    return jsonify({"code": 200, "msg": "Company data updated successfully"}), 200
            else:
                # Insert new company data
                company_data["created_date"] = datetime.utcnow()
                result = mongo_db.get_collection('companies').insert_one(company_data)
                company_data['company_id'] = str(result.inserted_id)
                
                return jsonify({"code": 201, "msg": "Company and admin data created successfully", "company_id": str(result.inserted_id)}), 201
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    return jsonify({"code": 404, "msg": "Function not found"}), 404


