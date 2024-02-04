import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

def send_email_notification(recipients, subject, title, content, url, test=True):

    if test:
        for r in recipients:           
            print(f"Would have sent notification to {r}")

        recipients = os.getenv('TEST_SUBSCRIBERS').split(';')

    for r in recipients:

        print(f"Actually sending notification to {r}")

        message = Mail(
        from_email=("lucas@meyerperin.org", "Lucas A. Meyer"),
        to_emails=[To(r)], is_multiple=True)

        message.dynamic_template_data = {
        "subject": subject,
        "title": title,
        "content": content,
        "post": url,
        }

        message.template_id = "d-f87c9767f8c641b082c2d4cbcff1f6ae"

        try:
            sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            sendgrid_client.send(message)
        except Exception as e:
            print(e)

