import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email config
MAIL_USERNAME = 'mahapatravinayak@gmail.com'
MAIL_PASSWORD = 'wrdb okdi macb zxim'

teachers = [
    {"name": "Rajesh Kumar", "email": "rajesh@vaanyan.com"},
    {"name": "Nitin Rawat", "email": "nitin.rawat2@gmail.com"},
    {"name": "Pankaj Kumar", "email": "pankaj.kumar@gmail.com"},
    {"name": "Siddhant Jajedi", "email": "siddhantjajedi98765@gmail.com"},
    {"name": "Mohammad Shadan", "email": "Mohdshadan.info@gmail.com"},
    {"name": "Shubham Sundriyal", "email": "shubhamsun1999@gmail.com"},
    {"name": "Deepa Rani", "email": "dhanipal19011015@gmail.com"},
    {"name": "Rakesh Yadav", "email": "rokyarjun4949@gmail.com"},
    {"name": "Sparsh Rawat", "email": "rawatsparsh079@gmail.com"},
    {"name": "Gangotri Bhaisora", "email": "jigangotri91@gmail.com"},
]

def send_email(teacher):
    msg = MIMEMultipart('alternative')
    msg['From'] = MAIL_USERNAME
    msg['To'] = teacher['email']
    msg['Subject'] = "Welcome to Vaanyan Home Tuition - Your Login Details"

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #6b21a8, #9333ea); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px;">🎓 Vaanyan Home Tuition</h1>
            <p style="color: #e9d5ff; margin: 8px 0 0;">Connecting Students with Great Teachers</p>
        </div>

        <div style="background: #ffffff; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <p style="font-size: 18px; color: #374151;">Dear <strong>{teacher['name']}</strong>,</p>

            <p style="color: #6b7280; line-height: 1.8;">
                Welcome to the <strong>Vaanyan Home Tuition</strong> family! We're thrilled to have you on board as one of our valued teachers.
            </p>

            <p style="color: #6b7280; line-height: 1.8;">
                We recently upgraded our platform and as part of this process, we have reset all teacher accounts. Please use the credentials below to log in and update your password.
            </p>

            <div style="background: #f3f4f6; border-radius: 10px; padding: 20px; margin: 20px 0; border-left: 4px solid #7c3aed;">
                <h3 style="color: #374151; margin: 0 0 15px;">🔐 Your Login Credentials</h3>
                <p style="margin: 8px 0; color: #374151;"><strong>Website:</strong> <a href="https://vaanyan.com/login" style="color: #7c3aed;">vaanyan.com</a></p>
                <p style="margin: 8px 0; color: #374151;"><strong>Email:</strong> {teacher['email']}</p>
                <p style="margin: 8px 0; color: #374151;"><strong>Password:</strong> <span style="background: #ede9fe; padding: 3px 8px; border-radius: 4px; font-family: monospace;">Vaanyan@123</span></p>
            </div>

            <div style="background: #fef3c7; border-radius: 10px; padding: 15px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                <p style="margin: 0; color: #92400e;">⚠️ <strong>Important:</strong> Please change your password after logging in for security.</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://vaanyan.com/login" 
                   style="background: linear-gradient(135deg, #6b21a8, #9333ea); color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
                    Login to Vaanyan →
                </a>
            </div>

            <p style="color: #6b7280; line-height: 1.8;">
                If you face any issues logging in, feel free to contact us at 
                <a href="mailto:mahapatravinayak@gmail.com" style="color: #7c3aed;">mahapatravinayak@gmail.com</a> 
                or call us at <strong>+91 7037714565</strong>.
            </p>

            <p style="color: #6b7280;">
                Warm regards,<br>
                <strong>Vinayak Mahapatra</strong><br>
                Vaanyan Home Tuition
            </p>
        </div>

        <p style="text-align: center; color: #9ca3af; font-size: 12px; margin-top: 20px;">
            © 2026 Vaanyan Home Tuition | vaanyan.com
        </p>
    </div>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {teacher['name']} ({teacher['email']})")
        return True
    except Exception as e:
        print(f"❌ Failed for {teacher['name']}: {e}")
        return False


# Send emails to all teachers
print("Sending welcome emails to all teachers...\n")
success = 0
failed = 0

for teacher in teachers:
    if send_email(teacher):
        success += 1
    else:
        failed += 1

print(f"\n🎉 Done! Sent: {success}, Failed: {failed}")