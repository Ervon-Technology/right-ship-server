from flask import Flask, render_template,send_from_directory, request, redirect, url_for, flash, session,jsonify,render_template_string,send_file
from db import mongo_db
from bson.objectid import ObjectId
from bson import ObjectId, json_util
from flask_cors import CORS
import os
from datetime import datetime
app = Flask(__name__,static_folder='static')

CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key =  os.environ.get('SECRET_KEY')

@app.route('/')
def default():
    return "Server running"

#for admin to create team members or to add/update/edit permissions
@app.route('/team/<function>', methods=['POST'])
def teamMembers(function):
    #  create team members
    if function.lower() == 'create':
        try:
            data = request.get_json()
            name = data.get('name')
            role = data.get('role', 'Employee')
            status = data.get('status', 'Active')
            joined_date = data.get('joined_date', datetime.utcnow().strftime('%d %b, %Y'))
            description = data.get('description')
            permissions = data.get('permissions', [])
            permission_ids = []

            if not name or not description:
                return jsonify({"code": 400, "error": "Name and description are required"}), 400

            if permissions:
                permissions_data = list(mongo_db.get_collection('permissions').find({"name": {"$in": permissions}}, {"_id": 1, "name": 1}))
                permissions_names = [perm['name'] for perm in permissions_data]
                permission_ids = [str(i['_id']) for i in permissions_data]

                # Find permissions that are not in the database
                perm_not_found = [perm for perm in permissions if perm not in permissions_names]
                if perm_not_found:
                    return jsonify({"code": 400, "msg": "Permission(s) not found: " + str(perm_not_found)}), 400

            team_member = {
                "name": name,
                "role": role,
                "status": status,
                "joined_date": joined_date,
                "description": description,
                "permissions": permissions,
                "permission_ids": permission_ids,
                "created_date": datetime.utcnow()
            }

            check_if_exists = mongo_db.get_collection('team').find_one({"name": name, "description": description}, {"_id": 0, "name": 1})
            if check_if_exists is None:
                mongo_db.get_collection('team').insert_one(team_member)
                del team_member['_id']
                return jsonify({"code": 200, "msg": "Team member created successfully", "team": team_member}), 201
            else:
                return {"code": 300, "msg": f"This user ({name}) is already registered as a team "}
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # add/update/edit permissions or any field like name or description
    elif function.lower() == 'edit':
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        del data['user_id']
        result = mongo_db.get_collection('team').update_one({"_id": ObjectId(user_id)}, {"$set": data})
        if result.modified_count == 0:
            return {"code": 202, "msg": "No data found for updates"}
        else:
            return {"code": 200, "msg": "Data updated for user " + user_id}

    elif function.lower() == 'delete':
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        result = mongo_db.get_collection('team').delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            return {"code": 202, "msg": "No data found for deletion"}
        else:
            return {"code": 200, "msg": "Data deleted for user " + user_id}

    elif function.lower() == 'get':
        try:
            data = request.get_json()
            user_id = data.get("user_id")
            if user_id:
                data['_id'] = ObjectId(data['user_id'])
                del data['user_id']
            result = list(mongo_db.get_collection('team').find(data))
            
            for i in result:
                i['user_id'] = str(i['_id'])
                i['_id'] = str(i['_id'])
                # Fetch and update latest permission names based on ids
                permission_names = list(mongo_db.get_collection('permissions').find({"_id": {"$in": [ObjectId(pid) for pid in i['permission_ids']]}}, {"_id": 0, "name": 1}))
                i['permissions'] = [p['name'] for p in permission_names]
                
            return {'code': 200, 'data': result, 'msg': "Successfully fetched team data"}
        except Exception as e:
            return {"code": 500, "msg": "Error: " + str(e)}

    return {"code": 404, "msg": "Method not found"}

@app.route('/permissions/<function>', methods=['POST'])
def permissions(function):
    if function.lower() == 'create':
        try:
            data = request.get_json()
            name = data.get('name')
            description = data.get('description')
            
            
            if not name or not description:
                return jsonify({"code":400,"error": "Name and description are required"}), 400
            
            permissions = {
                "name": name,
                "description": description,
                "created_date": datetime.now()
            }
            checkIfExists = mongo_db.get_collection('permissions').find_one({"name":name},{"_id":0,"name":1})
            if checkIfExists == None:
                mongo_db.get_collection('permissions').insert_one(permissions)   
                del permissions['_id']
                return jsonify({"code":200,"msg": "Permissions created successfully", "permissions": permissions}), 201
            else:
                return {"code":300,"msg":f"The name ({name}) has been already taken "}
        except Exception as e:
            return jsonify({"code":500,"error": str(e)}), 500
        
    # add/update/edit any field like name or description
    elif function.lower() == 'edit':
        data = request.get_json()
        permission_id = data.get('permission_id')
        if not permission_id :
            return jsonify({"error": "permission_id is required"}), 400
        del data['permission_id']
        
        result= mongo_db.get_collection('permissions').update_one({"_id":ObjectId(permission_id)},{"$set":data})
        if result.modified_count == 0:
            return {"code":202,"msg":"No data found for updates"}
        else:
            return {"code":200,"msg":"Data updated for permission "+permission_id}
        
    elif function.lower() == 'delete':
        data = request.get_json()
        permission_id = data.get('permission_id')
        if not permission_id:
            return jsonify({"error": "permission_id is required"}), 400
        
        try:
            result = mongo_db.get_collection('permissions').delete_one({"_id": ObjectId(permission_id)})
            if result.deleted_count == 0:
                return {"code":202,"msg":"No data found for deletion"}
            else:
                return {"code":200,"msg":"Data deleted for permission " + permission_id}
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    
    elif function.lower() == 'get':
        try:
            data = request.get_json()
            result= list(mongo_db.get_collection('permissions').find(data))
            for i in result:
                i['permission_id'] = str(i['_id'])
                i['_id'] = str(i['_id'])
            return {'code':200,'data':(result),'msg':"Successfully fetched permissions data"}
        except Exception as e:
            return {"code":500,"msg":"Pass {} in data or search query"}
    
    return {"code":404,"msg":"Method not found"}
        
    
@app.route('/subscription/<function>', methods=['POST'])
def subscriptions(function):
    if function.lower() == 'create':
        try:
            data = request.get_json()
            name = data.get('name')
            price = data.get('price')
            start_date = data.get('start_date', None)
            expire_date = data.get('expire_date', None)
            
            if not name or not price:
                return jsonify({"code": 400, "error": "Name and price are required"}), 400
            
            subscription = {
                "name": name,
                "price": price,
                "start_date": start_date,
                "expire_date": expire_date,
                "created_date": datetime.now()
            }
            check_if_exists = mongo_db.get_collection('subscription').find_one({"name": name})
            if check_if_exists is None:
                mongo_db.get_collection('subscription').insert_one(subscription)
                del subscription['_id']
                return jsonify({"code": 200, "msg": "Subscription created successfully", "subscription": subscription}), 201
            else:
                return {"code": 300, "msg": f"The subscription ({name}) already exists "}
        except Exception as e:
            return jsonify({"code": 500, "error": str(e)}), 500
        
    elif function.lower() == 'edit':
        data = request.get_json()
        subscription_id = data.get('subscription_id')
        if not subscription_id:
            return jsonify({"error": "subscription_id is required"}), 400
        del data['subscription_id']
        
        result = mongo_db.get_collection('subscription').update_one({"_id": ObjectId(subscription_id)}, {"$set": data})
        if result.modified_count == 0:
            return {"code": 202, "msg": "No data found for updates"}
        else:
            return {"code": 200, "msg": "Data updated for subscription " + subscription_id}
        
    elif function.lower() == 'delete':
        data = request.get_json()
        subscription_id = data.get('subscription_id')
        if not subscription_id:
            return jsonify({"error": "subscription_id is required"}), 400
        
        try:
            result = mongo_db.get_collection('subscription').delete_one({"_id": ObjectId(subscription_id)})
            if result.deleted_count == 0:
                return {"code": 202, "msg": "No data found for deletion"}
            else:
                return {"code": 200, "msg": "Data deleted for subscription " + subscription_id}
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif function.lower() == 'get':
        try:
            data = request.get_json()
            result = list(mongo_db.get_collection('subscription').find(data))
            for i in result:
                i['subscription_id'] = str(i['_id'])
                i['_id'] = str(i['_id'])
            return {'code': 200, 'data': result, 'msg': "Successfully fetched subscriptions data"}
        except Exception as e:
            return {"code": 500, "msg": "Pass {} in data or search query"}
    
    return {"code": 404, "msg": "Method not found"}   

@app.route('/attributes/<function>', methods=['POST'])
def attributes(function):
    if function.lower() == 'create':
        try:
            data = request.get_json()
            ship_categories = data.get('ship_categories', [])
            certificate_country_wise = data.get('certificate_country_wise', '')
            
            attribute = {
                "ship_categories": ship_categories,
                "certificate_country_wise": certificate_country_wise,
                "created_date": datetime.now()
            }
            check_if_exists = mongo_db.get_collection('attributes').find_one({"ship_categories": ship_categories,"certificate_country_wise": certificate_country_wise,})
            if check_if_exists is None:
                mongo_db.get_collection('attributes').insert_one(attribute)
                del attribute['_id']
                return jsonify({"code": 200, "msg": "Attribute created successfully", "attribute": attribute}), 201
            else:
                return {"code": 300, "msg": f"The ship_categories ({str(ship_categories)}) and certificate_country_wise {certificate_country_wise} already exists "}
            
        except Exception as e:
            return jsonify({"code": 500, "error": str(e)}), 500

    elif function.lower() == 'edit':
        data = request.get_json()
        attribute_id = data.get('attribute_id')
        if not attribute_id:
            return jsonify({"error": "attribute_id is required"}), 400
        del data['attribute_id']
        
        result = mongo_db.get_collection('attributes').update_one({"_id": ObjectId(attribute_id)}, {"$set": data})
        if result.modified_count == 0:
            return {"code": 202, "msg": "No data found for updates"}
        else:
            return {"code": 200, "msg": "Data updated for attribute " + attribute_id}

    elif function.lower() == 'delete':
        data = request.get_json()
        attribute_id = data.get('attribute_id')
        if not attribute_id:
            return jsonify({"error": "attribute_id is required"}), 400
        
        try:
            result = mongo_db.get_collection('attributes').delete_one({"_id": ObjectId(attribute_id)})
            if result.deleted_count == 0:
                return {"code": 202, "msg": "No data found for deletion"}
            else:
                return {"code": 200, "msg": "Data deleted for attribute " + attribute_id}
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif function.lower() == 'get':
        try:
            data = request.get_json()
            result = list(mongo_db.get_collection('attributes').find(data))
            for i in result:
                i['attribute_id'] = str(i['_id'])
                i['_id'] = str(i['_id'])
            return {'code': 200, 'data': result, 'msg': "Successfully fetched attributes data"}
        except Exception as e:
            return {"code": 500, "msg": "Pass {} in data or search query"}

    return {"code": 404, "msg": "Method not found"}


@app.route('/company/<function>',methods=['POST'])
def employersFn(function):
    from companyProfile.base import routes
    data = request.get_json()
    return routes(data,function)
    

if __name__ == '__main__':
    app.run(port=7800,host='0.0.0.0')