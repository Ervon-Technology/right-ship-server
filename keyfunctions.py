
from db import mongo_db
from flask import jsonify
from datetime import datetime
from datetime import timezone
from bson.objectid import ObjectId
from bson import ObjectId, json_util
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#check no existence
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

        return ({"code": 404, "msg": "User not found"})

    except Exception as e:
        return ({"code": 500, "msg": "Error: " + str(e)})
  
  
def sendCustomEmail(to_email, subject, body):
    try:
    

        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_username = 'neomanishchourasiya@gmail.com'
        smtp_password = 'oqdfgxqujhyleiap'
        sender_email = smtp_username

        message = MIMEMultipart()
        message['From'] = f"Rightship <{sender_email}>"
        message['To'] = to_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = message.as_string()
        server.sendmail(sender_email, to_email, text)
        print("MSG sent")
        server.quit()
        return {"code": 200, "msg": "Mail sent"}
    except Exception as e:
        return {"code": 500, "msg": str(e)}

