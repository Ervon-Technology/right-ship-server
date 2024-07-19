import http.client
import json

headers = {
    "Accept": "*/*",
    "User-Agent": "Python Client",
    "Content-Type": "application/json",
    "clientId": "H1VB7HNOG3L3RFY10E51QHVALKH9JAXV",  # Replace with your actual clientId
    "clientSecret": "tv1rx0435k7ve5ab11z8hjknkzh5auzj"  # Replace with your actual clientSecret
}

def send_otp(phone_number):
    conn = http.client.HTTPSConnection("auth.otpless.app")
    payload = json.dumps({
        "phoneNumber": phone_number,
        "otpLength": 6,
        "channel": "WHATSAPP",  # Can be SMS, WHATSAPP, or EMAIL
        "expiry": 600
    })
    try:
        conn.request("POST", "/auth/otp/v1/send", payload, headers)
        response = conn.getresponse()
        result = response.read()
        conn.close()
        res = json.loads(result)
        order_id = res.get('orderId')
        print("Send OTP Response:", {"code": 200, "order_id": order_id})
        return {"code": 200, "order_id": order_id}
    except Exception as e:
        return {"code": 500, "msg": str(e)}

def verify_otp(phone_number, otp, order_id):
    conn = http.client.HTTPSConnection("auth.otpless.app")
    payload = json.dumps({
        "phoneNumber": phone_number,
        "otp": otp,
        "orderId": order_id
    })

    conn.request("POST", "/auth/otp/v1/verify", payload, headers)
    response = conn.getresponse()
    result = response.read()
    conn.close()

    result = json.loads(result)
    print("Verify OTP Response:", result)
    
    if response.status == 200 and result.get('isOTPVerified') == True:
        return {"code": 200, "msg": "OTP verified successfully"}
    else:
        if result["message"] ==  "The OTP for this order has already verified!":
            result['code'] = 201 # if already verified
        else:
            result['code'] =400
        return result
        

# Example usage for testing
# response = send_otp("916206630515")
# order_id = response.get('order_id')  # Store this for verification
# print("Order ID:", order_id)

# After receiving the OTP on your device, call the verify function with the OTP and order ID
# verify_response = verify_otp("916206630515", "349539", "Otp_C4BB710D3A464A0F8E4313A876EE7AAA")  # Replace "123456" with the OTP received
# print(verify_response)