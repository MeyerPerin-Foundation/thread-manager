from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()   

STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("THREADS_CONTAINER_NAME")

connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
container_name = CONTAINER_NAME

def convert_timestamp(unix_timestamp):
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def process_data(data):
    try:

        posts = data.get('text_post_app_text_posts', [])

        # Iterate through each entry in the JSON data
        for entry in posts:
            # Check if 'media' key exists
            if 'media' in entry:
                for media_item in entry['media']:
                    uri = media_item.get('uri', 'No URI')
                    title = media_item.get('title', 'No Title')
                    timestamp = convert_timestamp(media_item.get('creation_timestamp', 0))

                    print(f"Media URI: {uri}")
                    print(f"Media Title: {title}")
                    print(f"Timestamp: {timestamp}")
                    print("----------")

            # Extract the general title and timestamp outside the media list if it exists
            if 'title' in entry:
                general_title = entry.get('title', 'No General Title')
                general_timestamp = convert_timestamp(entry.get('creation_timestamp', 0))

                print(f"General Title: {general_title}")
                print(f"General Timestamp: {general_timestamp}")
                print("----------")

    except json.JSONDecodeError:
        print("Invalid JSON")

# Create a BlobServiceClient using the connection string
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Access the container
container_client = blob_service_client.get_container_client(container_name)

# List the blobs in the container
blob_list = container_client.list_blobs()
i = 0
for blob in blob_list:
    i += 1
    print(f"Processing blob {i}")
    if blob.name.endswith("threads_and_replies.json"):
        blob_client = container_client.get_blob_client(blob.name)
        blob_content = blob_client.download_blob().readall()
        blob_json = json.loads(blob_content)
        process_data(blob_json)
    
