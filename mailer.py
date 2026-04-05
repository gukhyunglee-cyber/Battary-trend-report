import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import settings

import os
from email.mime.base import MIMEBase
from email import encoders

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = getattr(settings, 'EMAIL_SENDER', None)
        self.password = getattr(settings, 'EMAIL_PASSWORD', None)
        
    def send_email(self, recipient: str, subject: str, body: str, attachment_path: str = None):
        if not self.sender_email or not self.password:
            print("[Mailer] Email credentials not set in settings.py. Skipping email.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))
            
            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                msg.attach(part)
                print(f"[Mailer] Attached file: {filename}")

            print(f"[Mailer] Sending email to {recipient}...")
            
            # Parse multiple recipients if comma-separated
            to_addrs = [r.strip() for r in recipient.split(',')]
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_addrs, text)
            server.quit()
            
            print("[Mailer] Email sent successfully!")
            return True
        except Exception as e:
            print(f"[Mailer] Failed to send email: {e}")
            import traceback
            traceback.print_exc()
            return False
