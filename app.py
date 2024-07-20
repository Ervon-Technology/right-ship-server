from flask import Flask, render_template,send_from_directory, request, redirect, url_for, flash, session,jsonify,render_template_string,send_file
from db import mongo_db
from bson.objectid import ObjectId
from bson import ObjectId, json_util
from flask_cors import CORS
import uuid
from dotenv import load_dotenv
import sys
import boto3
from werkzeug.utils import secure_filename
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
import os
from datetime import datetime
from datetime import  timezone
app = Flask(__name__,static_folder='static')

CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key =  os.environ.get('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
load_dotenv()

s3_client = boto3.client(
    's3',
    config=Config(signature_version='s3v4'),
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name = os.getenv('AWS_REGION')
)

app.config['S3_BUCKET'] = 'rs-file-uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def default():
    return "Server running"

#for getting user info
@app.route('/user/details', methods=['POST'])
def get_user_details():
    try:
        data = request.get_json()
        mobile_no = data.get('mobile_no')
        user_type = data.get('user_type')

        if not mobile_no or not user_type:
            return jsonify({"code": 400, "error": "mobile_no and user_type are required"}), 400

        user_type_to_collection = {
            "employee": "employee",
            "company": "company_team",
            "admin": "team"
        }

        collection_name = user_type_to_collection.get(user_type.lower())

        if not collection_name:
            return jsonify({"code": 400, "error": "Invalid user_type"}), 400

        user_data = mongo_db.get_collection(collection_name).find_one({"mobile_no": mobile_no}, {"_id": 0})

        if not user_data:
            return jsonify({"code": 404, "msg": "User not found"}), 404

        return jsonify({"code": 200, "data": user_data}), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Error: " + str(e)}), 500 

@app.route('/otp/<function>', methods=['POST'])
def otpFn(function):
    from sendOtp import send_otp, verify_otp
    if function.lower() == 'send_otp':
        data = request.get_json()
        phone_number = data.get('mobile_no', '')
        if not phone_number:
            return {"code": 400, "error": "mobile_no key not defined"}
        
        phone_number = str(phone_number)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Send OTP
        response = send_otp(phone_number)
        if response.get('code') != 200:
            return response

        order_id = response.get('order_id')
        if not order_id:
            return {"code": 500, "error": "Failed to send OTP"}

        # Store the order_id and phone number temporarily
        mongo_db.get_collection('otp_sessions').insert_one({
            "mobile_no": phone_number,
            "order_id": order_id,
            "created_date": datetime.now(timezone.utc)
        })

        return {"code": 200, "msg": "OTP sent successfully"}

    elif function.lower() == 'verify_otp':
        data = request.get_json()
        phone_number = data.get('mobile_no', '')
        otp = data.get('otp', '')
        if not phone_number or not otp:
            return {"code": 400, "error": "mobile_no and otp keys are required"}
        
        phone_number = str(phone_number)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Retrieve the order_id from the temporary storage
        session = mongo_db.get_collection('otp_sessions').find_one({"mobile_no": phone_number}, sort=[("created_date", -1)])
        if not session:
            return {"code": 404, "error": "No OTP session found for this number"}

        order_id = session.get('order_id')
        
        # Verify OTP
        response = verify_otp(phone_number, otp, order_id)
        if response.get('code') != 200:
            return response
        
        # Mark OTP session as verified
        mongo_db.get_collection('otp_sessions').update_one(
            {"mobile_no": phone_number},
            {"$set": {"verified": True}}
        )

        return {"code": 200, "msg": "OTP verified successfully"}
    
    return {'code': 404, "msg": "Method not defined"}

@app.route('/admin/<function>', methods=['POST'])
def adminFn(function):
    if function.lower() == 'register':
        data = request.get_json()
        mobile_no = data.get('mobile_no', '')
        if not mobile_no:
            return {"code": 400, "error": "mobile_no key not defined"}
        
        phone_number = str(mobile_no)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Check if the OTP session is verified
        session = mongo_db.get_collection('otp_sessions').find_one({"mobile_no": phone_number, "verified": True}, sort=[("created_date", -1)])
        if not session:
            return {"code": 400, "error": "OTP not verified"}
        
        team_member = {
            "role": "super_admin",
            "status": "active",
            "mobile_no": mobile_no,
            "joined_date": datetime.now(timezone.utc).strftime('%d %b, %Y'),
            "created_date": datetime.now(timezone.utc)
        }

        # Check if the user already exists
        check_if_exists = mongo_db.get_collection('team').find_one({"mobile_no": mobile_no}, {"_id": 0, "mobile_no": 1})
        if check_if_exists is None:
            mongo_db.get_collection('team').insert_one(team_member)
            del team_member['_id']
            return jsonify({"code": 200, "msg": "Admin created successfully", "team": team_member})
        else:
            return {"code": 300, "msg": f"This user ({phone_number}) is already registered as an admin"}

    if function.lower() == 'login':
        data = request.get_json()
        mobile_no = data.get('mobile_no', '')
        if not mobile_no:
            return {"code": 400, "error": "mobile_no key not defined"}
        
        phone_number = str(mobile_no)
        if len(phone_number) == 10:
            phone_number = f"91{phone_number}"  # for India auto input
        
        # Check if the OTP session is verified
        session = mongo_db.get_collection('otp_sessions').find_one({"mobile_no": phone_number, "verified": True}, sort=[("created_date", -1)])
        if not session:
            return {"code": 400, "error": "OTP not verified"}
        
        

        # Check if the user already exists
        check_if_exists = mongo_db.get_collection('team').find_one({"mobile_no": mobile_no}, {"_id": 0})
        if check_if_exists is None:
            return jsonify({"code": 500, "msg": "Number not registered"})
        else:
            
            return {"code": 200, "msg": f"Admin with ({phone_number}) login successfull ","data":check_if_exists}

    return {'code': 404, "msg": "Method not defined"}

@app.route('/company/register', methods=['POST'])
def companyRegister():
    try:
        from companyProfile.sendEmail import send_email 
        data = request.get_json()
        mobile_no = data.get('mobile_no')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        company_name = data.get('company_name')
        website_url = data.get('website_url')
        city = data.get('city')
        state = data.get('state')
        country = data.get('country')
        license_rpsl = data.get('license_rpsl', '')
        address = data.get('address')

        if not mobile_no or not email or not first_name or not company_name:
            return jsonify({"error": "mobile_no, first_name, company_name, and email are required"}), 400

        # Create verification link
        verification_token = os.urandom(24).hex()
        verification_url = f"https://api.rightships.com/verify_email?token={verification_token}"

        # Prepare the registration data
        registration_data = {
            "first_name": first_name,
            "last_name": last_name,
            "company_name": company_name,
            "website_url": website_url,
            "mobile_no": mobile_no,
            "email": email,
            "city": city,
            "state": state,
            "country": country,
            "license_rpsl": license_rpsl,
            "address": address,
            "verification_token": verification_token,
            "verified": False,
            "created_date": datetime.now(timezone.utc)
        }

        # Insert registration data into temporary collection
        mongo_db.get_collection('registration_sessions').insert_one(registration_data)

        # Send verification email
        res = send_email(email, 'Welcome to Rightship', verification_url, first_name, company_name)
        return res

    except Exception as e:
        return jsonify({"code": 500, "msg": "Error: " + str(e)})

@app.route('/verify_email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({"code": 400, "error": "Token is required"}), 400

    # Find the registration session by token
    session = mongo_db.get_collection('registration_sessions').find_one({"verification_token": token})

    if not session:
        return jsonify({"code": 404, "error": "Invalid or expired token"}), 404

    # Create company data
    company_data = {key: session[key] for key in session if key != '_id' and key != 'verification_token'}
    company_data['verified'] = True

    # Insert company data into companies collection
    company_result = mongo_db.get_collection('companies').insert_one(company_data)
    company_id = str(company_result.inserted_id)

    # Create admin data
    admin_data = {
        "mobile_no": company_data['mobile_no'],
        "role": "admin",
        "status": "active",
        "company_id": company_id,
        "created_date": datetime.now(timezone.utc)
    }

    admin_result = mongo_db.get_collection('company_team').find_one_and_update(
        {"mobile_no": company_data['mobile_no']},
        {"$setOnInsert": admin_data},
        upsert=True,
        return_document=True
    )
    company_data['company_admin_id'] = str(admin_result['_id'])

    # Update the company document with the admin ID
    mongo_db.get_collection('companies').update_one(
        {"_id": company_result.inserted_id},
        {"$set": {"company_admin_id": company_data['company_admin_id']}}
    )

    # Remove the session after verification
    mongo_db.get_collection('registration_sessions').delete_one({"_id": session['_id']})

    return jsonify({"code": 200, "msg": "Email verified and company created successfully"}), 200

#for admin to create team members or to add/update/edit permissions
@app.route('/team/<function>', methods=['POST'])
def teamMembers(function):
    #  create team members
    if function.lower() == 'create':
        try:
            data = request.get_json()
            name = data.get('name')
            role = data.get('role', 'Employee')
            mobile_no = data.get('mobile_no')
            email = data.get('email')
            status = data.get('status', 'Pending')
            joined_date = data.get('joined_date', datetime.utcnow().strftime('%d %b, %Y'))
            description = data.get('description','')

            if not name  or not mobile_no or not email or not role or not status:
                return jsonify({"code": 400, "error": "Name,mobile_no,email,role and status are required"}), 400

           
            team_member = {
                "name": name,
                "role": role,
                "mobile_no": mobile_no,
                "email": email,
                "status": status,
                "joined_date": joined_date,
                "description": description,
                "created_date": datetime.utcnow()
            }

            check_if_exists = mongo_db.get_collection('team').find_one({"mobile_no": mobile_no}, {"_id": 0, "name": 1})
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
               
                
            return {'code': 200, 'data': result, 'msg': "Successfully fetched team data"}
        except Exception as e:
            return {"code": 500, "msg": "Error: " + str(e)}

    return {"code": 404, "msg": "Method not found"}

   
    
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
            
            # subscription = {
            #     "name": name,
            #     "price": price,
            #     "start_date": start_date,
            #     "expire_date": expire_date,
            #     "created_date": datetime.now()
            # }
            check_if_exists = mongo_db.get_collection('subscription').find_one({"name": name})
            if check_if_exists is None:
                mongo_db.get_collection('subscription').insert_one(data)
                if '_id' in list(data):
                    del data['_id']
                return jsonify({"code": 200, "msg": "Subscription created successfully", "subscription": data}), 201
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

            # Create a query to check for duplicates
            query = {key: data[key] for key in data.keys()}

            # Check if the document already exists
            check_if_exists = mongo_db.get_collection('attributes').find_one(query)
            if check_if_exists is None:
                data["created_date"] = datetime.now()
                mongo_db.get_collection('attributes').insert_one(data)
                del data['_id']
                return jsonify({"code": 200, "msg": "Attribute created successfully", "attribute": data}), 201
            else:
                return {"code": 300, "msg": "The attribute already exists with the given keys"}
            
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
    
@app.route('/company/team/<function>', methods=['POST'])
def team_operations(function):
    from companyProfile.base import teamroutes
    data = request.get_json()
    return teamroutes(data,function)

@app.route('/company/attributes/<function>', methods=['POST'])
def attributes_operations(function):
    from companyProfile.base import attributeroutes
    data = request.get_json()
    return attributeroutes(data,function)
    
@app.route('/company/application/<function>', methods=['POST'])
def application_operations(function):
    from companyProfile.base import applicationRoutes
    data = request.get_json()
    return applicationRoutes(data,function)


#for employee
@app.route('/employee/<function>',methods=['POST'])
def employeeFn(function):
    from employeeProfile.base import routes
    data = request.get_json()
    return routes(data,function)
#for file-uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        unique_id = str(uuid.uuid4())
        filename = secure_filename(f"{unique_id}_{file.filename}")

        try:
            # Upload the file to S3
            s3_client.upload_fileobj(
                file,
                app.config['S3_BUCKET'],
                filename
            )
            s3_url = f'https://{app.config["S3_BUCKET"]}.s3.amazonaws.com/{filename}'
            return jsonify({'message': 'File successfully uploaded', 'file_url': s3_url}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400 
if __name__ == '__main__':
    app.run(port=7800,host='0.0.0.0')