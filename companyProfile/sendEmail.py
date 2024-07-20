import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(to_email, subject, verification_url, name, company_name):
    try:
        body = f'''
            Hello {name},
            <br><br>
            Thank you for registering your company - {company_name} with Rightship.
            <br><br>
            Please verify your email by clicking the following <a href="{verification_url}">link</a>.
            <br><br>
            Best regards,<br>
            Rightship
        '''

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

# send_email("support@cloudbelly.in", 'Welcome to Rightship', "http://65.0.167.98/support@cloudbelly.in", "Aniket", "Cloudbelly")