import requests
from dotenv import load_dotenv
import os
import hubspot
from pprint import pprint
from hubspot.crm.contacts import BatchReadInputSimplePublicObjectId, ApiException
import json

def filter_contacts_with_blog_subscription(contacts):
    filtered_contacts = [
        {
            "firstname": contact['properties']['firstname'],
            "lastname": contact['properties']['lastname'],
            "email": contact['properties']['email']
        }
        for contact in contacts
        if contact['properties'].get('blog_subscriber') == 'true'
    ]
    return filtered_contacts

def get_subscribed_contacts():
    load_dotenv()
    client = hubspot.Client.create(access_token=os.getenv("HUBSPOT_API_KEY"))
    all_contacts = client.crm.contacts.get_all(properties=["blog_subscriber", "email", "firstname", "lastname", "company"])
    dict_contacts = [contact.to_dict() for contact in all_contacts]
    filtered_contacts = filter_contacts_with_blog_subscription(dict_contacts)
    return filtered_contacts
