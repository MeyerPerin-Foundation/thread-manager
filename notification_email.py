import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Email
import mailchimp_marketing as Mailchimp
from mailchimp_marketing.api_client import ApiClientError


def getSubscribers():

    api_key = os.getenv('MAILCHIMP_API_KEY')  
    list_id = os.getenv('MAILCHIMP_LIST_ID')

    subscribers = []

    try:
        # Configure API key
        client = Mailchimp.Client()
        client.set_config({
            "api_key": api_key,
            "server": api_key.split('-')[1]  # Extract server prefix from API key
        })

        # Get contacts from a list
        response = client.lists.get_list_members_info(list_id)
        contacts = response['members']

        # Print or process contacts here
        for contact in contacts:
            if contact['status'] == 'subscribed':
                subscribers.append(contact['email_address'])
                print (f"Added subscriber: {contact['email_address']}")

    except ApiClientError as error:
        print(f"An error occurred: {error.text}")

    return subscribers


def sendNotification(recipients, test=True):

    if test:
        for r in recipients:           
            print(f"Would have sent notification to {r}")

        recipients = os.getenv('TEST_SUBSCRIBERS').split(';')

    for r in recipients:

        print(f"Actually sending notification to {r}")

        message = Mail(
        from_email=("lucas@meyerperin.com", "Lucas A. Meyer"),
        to_emails=[To(r)], is_multiple=True)

        message.dynamic_template_data = {
        "subject": "New blog post: Kindle Scribe",
        "title": "Kindle Scribe versus reMarkable 2",
        "content": "The main problem for me was the lack of a backlight, which made it hard to read in low light conditions, and even in somewhat normal light conditions — the contrast is not very good and not adjustable. The Kindle Scribe solves this problem.\n\nIn addition, the Kindle Scribe gives you access to the Kindle store, which means you can read most books on it.",
        "post": "https://www.meyerperin.com/posts/2024-01-12-kindle-scribe.html",
        }

        message.template_id = "d-f87c9767f8c641b082c2d4cbcff1f6ae"

        try:
            sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            sendgrid_client.send(message)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    load_dotenv()
    recipients = getSubscribers()
    sendNotification(recipients)
