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
            description = data.get('description')
            permissions = data.get('permissions', [])
            permission_ids = []
            if not name or not description:
                return jsonify({"code":400,"error": "Name and description are required"}), 400
            if permissions != []:
               
                permissions_data = list(mongo_db.get_collection('permissions').find({"name": {"$in": permissions}}, {"_id": 1, "name": 1}))
                permissions_names = [perm['name'] for perm in permissions_data]
                for i in permissions_data:
                    print(i)
                    permission_ids.append(str(i['_id'])) 
                
                # Find permissions that are not in the database
                perm_not_found = [perm for perm in permissions if perm not in permissions_names]
                if perm_not_found:
                    return jsonify({"code": 400, "msg": "Permission(s) not found: " + str(perm_not_found)}), 400
        
                        
            team = {
                "name": name,
                "description": description,
                "permissions": permissions,
                "created_date": datetime.utcnow(),
                "permission_ids":permission_ids
            }
            checkIfExists = mongo_db.get_collection('team').find_one({"name":name, "description": description},{"_id":0,"name":1})
            if checkIfExists == None:
                mongo_db.get_collection('team').insert_one(team)
                del team['_id']
                return jsonify({"code":200,"msg": "Team created successfully", "team": team}), 201
            else:
                return {"code":300,"msg":f"This user ({name}) is already registered as a team "}
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    # add/update/edit permissions or any field like name or description
    elif function.lower() == 'edit':
        data = request.get_json()
        user_id = data.get("user_id")
        if not user_id :
            return jsonify({"error": "user_id is required"}), 400
        del data['user_id']
        result= mongo_db.get_collection('team').update_one({"_id":ObjectId(user_id)},{"$set":data})
        if result.modified_count == 0:
            return {"code":202,"msg":"No data found for updates"}
        else:
            return {"code":200,"msg":"Data updated for user "+user_id}
    
    elif function.lower() == 'get':
        try:
            # add functionality to check permission from ids and update the latest permission name
            data = request.get_json()
            print(data)
            user_id = data.get("user_id")
            if user_id:
                data['_id'] = ObjectId(data['user_id'])
                del data['user_id']
            result= list(mongo_db.get_collection('team').find(data))
            
            for i in result:
                i['user_id'] = str(i['_id'])
                i['_id'] = str(i['_id'])
                # add functionality to check permission from ids and update the latest permission name here (Later not urgent )
            return {'code':200,'data':(result),'msg':"Successfully fetched team data"}
        except Exception as e:
            return {"code":500,"msg":"Pass {} in data or search query"}
    
    return {"code":404,"msg":"Method not found"}
            
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
        
    

if __name__ == '__main__':
    app.run(port=7800,host='0.0.0.0')