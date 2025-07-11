# email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def send_email_via_smtp(self, sender_email, app_password, recipient_email, subject, body):
        """
        Sends a single email using Gmail SMTP_SSL.
        Requires an App Password for Gmail if 2FA is enabled.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender_email, app_password)
                smtp.send_message(msg)
            return True, "Email sent successfully."
        except Exception as e:
            return False, str(e)

# Instantiate the EmailSender
email_manager = EmailSender()
