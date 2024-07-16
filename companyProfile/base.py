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
            {"_id": ObjectId(company_id)} if company_id else {"mobile_no": payload.get('mobile_no')},
            {"$set": payload},
            upsert=True
        )
        
        if result.upserted_id:
            company_id = str(result.upserted_id)
            return jsonify({"code": 200, "msg": "Company data created successfully", "company_id": company_id}), 200
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
                "role":"admin",
                "status":"active",
                "created_date": datetime.utcnow()
            }
            admin_result = mongo_db.get_collection('company_team').find_one_and_update(
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
                
                return jsonify({"code": 200, "msg": "Company and admin data created successfully", "company_id": str(result.inserted_id)}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    
    else:
        return jsonify({"error": "Invalid function"}), 400
    return jsonify({"code": 404, "msg": "Function not found"}), 404

def teamroutes(payload,function):
    if function == 'add':
        try:
            team_id = payload.get('team_id', '')
            company_id = payload.get('company_id')
            mobile_no = payload.get('mobile_no')
            if not mobile_no or not company_id:
                return jsonify({"code": 400, "msg": "Mobile no and company_id is required"}), 400
            
            created_date = datetime.utcnow()
            payload["created_date"] = created_date
            payload["company_id"] = company_id

            # Check for existing team member with the same mobile number
            existing_member = mongo_db.get_collection('company_team').find_one({"mobile_no": mobile_no,"company_id":company_id})

            if existing_member:
                # Update the existing member
                result = mongo_db.get_collection('company_team').update_one(
                    {"_id": existing_member["_id"]},
                    {"$set": payload}
                )
                payload['team_id'] = str(existing_member["_id"])
            else:
                # Insert new team member
                result = mongo_db.get_collection('company_team').insert_one(payload)
                payload['team_id'] = str(result.inserted_id)
            if '_id' in list(payload):
                del payload['_id']
            return jsonify({"code": 200, "msg": "Team member added/updated successfully", "team_member": payload}), 200

        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function == 'edit':
        try:
            team_id = payload.get('team_id')
            if not team_id:
                return jsonify({"error": "team_id is required"}), 400

            update_data = {key: value for key, value in payload.items() if key != 'team_id'}
            update_data["updated_date"] = datetime.utcnow()
            
            result = mongo_db.get_collection('company_team').update_one(
                {"_id": ObjectId(team_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return jsonify({"code": 202, "msg": "No data found for updates"}), 202
            else:
                return jsonify({"code": 200, "msg": "Team member updated successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function == 'delete':
        try:
            team_id = payload.get('team_id')
            if not team_id:
                return jsonify({"error": "team_id is required"}), 400
            
            result = mongo_db.get_collection('company_team').delete_one({"_id": ObjectId(team_id)})
            if result.deleted_count == 0:
                return jsonify({"code": 202, "msg": "No team member found for deletion"}), 202
            else:
                return jsonify({"code": 200, "msg": "Team member deleted successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

   
    
    elif function.lower() == 'get':
        try:
            team_id = payload.get('team_id', '')
            company_id = payload.get('company_id')
            if not company_id:
                return jsonify({"code": 400, "msg": "company_id is required"}), 400
            
            if team_id:
                team_member = mongo_db.get_collection('company_team').find_one({"_id": ObjectId(team_id), "company_id": company_id})
                if not team_member:
                    return jsonify({"code": 404, "msg": "Team member not found"}), 404
                team_member['_id'] = str(team_member['_id'])
                return jsonify({"code": 200, "team_member": team_member}), 200
            else:
                team_members = list(mongo_db.get_collection('company_team').find({"company_id": company_id}))
                for member in team_members:
                    member['_id'] = str(member['_id'])
                return jsonify({"code": 200, "team_members": team_members}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500
    else:
        return jsonify({"error": "Invalid function"}), 400

    return jsonify({"code": 404, "msg": "Function not found"}), 404


def attributeroutes(payload,function):
    if function == 'create':
        try:
            ship_types = payload.get('ship_types', [])
            ranks = payload.get('ranks', [])
            company_id = payload.get('company_id')
            if not company_id:
                return jsonify({"code": 400, "msg": "company_id is required"}), 400

            created_date = datetime.utcnow()
            payload["created_date"] = created_date
            payload["company_id"] = company_id

            # Perform upsert operation to avoid duplicates
            result = mongo_db.get_collection('company_attributes').update_one(
                {"company_id": company_id},
                {"$set": payload},
                upsert=True
            )

            if result.upserted_id:
                payload['attributes_id'] = str(result.upserted_id)
            else:
                existing_record = mongo_db.get_collection('company_attributes').find_one({"company_id": company_id})
                payload['attributes_id'] = str(existing_record['_id'])

            if '_id' in payload:
                del payload['_id']

            return jsonify({"code": 200, "msg": "Attributes created/updated successfully", "attributes": payload}), 200

        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500
        
    elif function == 'edit':
        try:
            attributes_id = payload.get('attributes_id')
            if not attributes_id:
                return jsonify({"error": "attributes_id is required"}), 400

            update_data = {key: value for key, value in payload.items() if key != 'attributes_id'}
            update_data["updated_date"] = datetime.utcnow()
            
            result = mongo_db.get_collection('company_attributes').update_one(
                {"_id": ObjectId(attributes_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return jsonify({"code": 202, "msg": "No data found for updates"}), 202
            else:
                return jsonify({"code": 200, "msg": "Attributes updated successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function == 'delete':
        try:
            attributes_id = payload.get('attributes_id')
            if not attributes_id:
                return jsonify({"error": "attributes_id is required"}), 400
            
            result = mongo_db.get_collection('company_attributes').delete_one({"_id": ObjectId(attributes_id)})
            if result.deleted_count == 0:
                return jsonify({"code": 202, "msg": "No attributes found for deletion"}), 202
            else:
                return jsonify({"code": 200, "msg": "Attributes deleted successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function.lower() == 'get':
        try:
            company_id = payload.get('company_id')
            if not company_id:
                return jsonify({"code": 400, "msg": "company_id is required"}), 400
            
            attributes = list(mongo_db.get_collection('company_attributes').find({"company_id": company_id}))
            for attr in attributes:
                attr['_id'] = str(attr['_id'])
            return jsonify({"code": 200, "attributes": attributes}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    else:
        return jsonify({"error": "Invalid function"}), 400
    return jsonify({"code": 404, "msg": "Function not found"}), 404


def applicationRoutes(payload,function):
    if function == 'create':
        try:
            company_id = payload.get('company_id')
            ship_types = payload.get('ship_types')
            ranks = payload.get('ranks')
            benefits = payload.get('benefits')
            description = payload.get('description')
            
            if not company_id or not ship_types or not ranks or not benefits or not description:
                return jsonify({"code": 400, "msg": "company_id, ship_types, ranks, benefits, and description are required"}), 400

            created_date = datetime.utcnow()
            payload["created_date"] = created_date
            payload["company_id"] = company_id

            # Check for existing application with the same details
            existing_application = mongo_db.get_collection('job_application').find_one({
                "company_id": company_id,
                "ship_types": ship_types,
                "ranks": ranks,
                "benefits": benefits,
                "description": description
            })

            if existing_application:
                # Update the existing application
                result = mongo_db.get_collection('job_application').update_one(
                    {"_id": existing_application["_id"]},
                    {"$set": payload}
                )
                payload['application_id'] = str(existing_application["_id"])
            else:
                # Insert new application
                result = mongo_db.get_collection('job_application').insert_one(payload)
                payload['application_id'] = str(result.inserted_id)
                
            if '_id' in list(payload):
                del payload['_id']

            return jsonify({"code": 200, "msg": "Application created/updated successfully", "application": payload}), 200

        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function == 'edit':
        try:
            application_id = payload.get('application_id')
            if not application_id:
                return jsonify({"error": "application_id is required"}), 400

            update_data = {key: value for key, value in payload.items() if key != 'application_id'}
            update_data["updated_date"] = datetime.utcnow()
            
            result = mongo_db.get_collection('job_application').update_one(
                {"_id": ObjectId(application_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return jsonify({"code": 202, "msg": "No data found for updates"}), 202
            else:
                return jsonify({"code": 200, "msg": "Application updated successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function == 'delete':
        try:
            application_id = payload.get('application_id')
            if not application_id:
                return jsonify({"error": "application_id is required"}), 400
            
            result = mongo_db.get_collection('job_application').delete_one({"_id": ObjectId(application_id)})
            if result.deleted_count == 0:
                return jsonify({"code": 202, "msg": "No application found for deletion"}), 202
            else:
                return jsonify({"code": 200, "msg": "Application deleted successfully"}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    elif function.lower() == 'get':
        try:
            company_id = payload.get('company_id')
            application_id = payload.get('application_id', '')
            
            if not company_id:
                return jsonify({"code": 400, "msg": "company_id is required"}), 400

            if application_id:
                application = mongo_db.get_collection('job_application').find_one({"_id": ObjectId(application_id), "company_id": company_id})
                if not application:
                    return jsonify({"code": 404, "msg": "Application not found"}), 404
                application['_id'] = str(application['_id'])
                application['application_id'] = str(application['_id'])
                return jsonify({"code": 200, "application": application}), 200
            else:
                applications = list(mongo_db.get_collection('job_application').find({"company_id": company_id}))
                for app in applications:
                    app['_id'] = str(app['_id'])
                    app['application_id'] = str(app['_id'])
                return jsonify({"code": 200, "applications": applications}), 200
        except Exception as e:
            return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500

    else:
        return jsonify({"error": "Invalid function"}), 400
    return jsonify({"code": 404, "msg": "Function not found"}), 404
