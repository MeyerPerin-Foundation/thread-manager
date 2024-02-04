import xml.etree.ElementTree as ET
import requests
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

def read_and_parse_xml(root):
    # Extract all URLs (loc elements) from the XML
    urls = [url.text for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    return urls

def find_differences(new, old):
    online_urls = read_and_parse_xml(new)
    local_urls = read_and_parse_xml(old)    

    # Find URLs that are unique to each list
    new_urls = set(online_urls) - set(local_urls)

    # filter new_urls and keep only those that contain /posts/
    new_urls = [url for url in new_urls if "/posts/" in url]
    return new_urls

def read_file_from_url(url):
    # Read a file from a URL
    response = requests.get(url)
    response.raise_for_status()  # This will raise an error if the fetch failed

    xml_content = ET.fromstring(response.content)
    return xml_content

def read_file_from_azstorage(path):
    load_dotenv()

    STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
    STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
    CONTAINER_NAME = os.getenv("SITEMAPS_CONTAINER_NAME")
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    container_name = CONTAINER_NAME

    # Create a BlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Access the container
    container_client = blob_service_client.get_container_client(container_name)
    # List the blobs in the container
    blob_client = container_client.get_blob_client(path)
    blob_content = blob_client.download_blob().readall()

    xml_content = ET.fromstring(blob_content)
    return xml_content


def main():
# Find URLs that are different between the two files
    new = read_file_from_url("https://meyerperin.org/sitemap.xml")
    old = read_file_from_azstorage("0d41257f-49ff-40f3-970e-2d1ebb8ccc22/meyerperin.org/sitemap.xml")

    new_urls = find_differences(new, old)

    # Output the differences
    print("New URLs:")
    for url in new_urls:
        print(url)

if __name__ == "__main__":
    main()    

