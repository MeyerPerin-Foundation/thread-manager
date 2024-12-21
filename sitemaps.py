import xml.etree.ElementTree as ET
import requests
from azure.storage.blob import BlobServiceClient
import app_config
from cosmosdb import BlogPosts
import logging

logger = logging.getLogger("tm-sitemaps")

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

def read_sitemap_from_url(url):
    # Read a file from a URL
    response = requests.get(url)
    response.raise_for_status()  # This will raise an error if the fetch failed

    xml_content = ET.fromstring(response.content)
    return xml_content

def read_sitemap_from_azstorage(path):
    blob_service_client = BlobServiceClient.from_connection_string(app_config.STORAGE_CONNECTION_STRING)
    blob_container = blob_service_client.get_container_client("sitemaps")
    blob_content = blob_container.download_blob(path).readall()
    xml_content = ET.fromstring(blob_content)
    return xml_content

def upload_to_azure_storage(blob_service_client, container_name, blob_name, data):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)
    blob_url = blob_client.url
    return blob_url

def save_sitemap_file_to_azure_storage(sitemap_url):
    
    blob_service_client = BlobServiceClient.from_connection_string(app_config.STORAGE_CONNECTION_STRING)
    sitemap_content = requests.get(sitemap_url).text

    # get the webesite name and the xml
    website_name = sitemap_url.split("//")[1].split("/")[0]
    sitemap_name = sitemap_url.split("/")[-1]
    blob_name = f"{website_name}/{sitemap_name}"
    blob_url = upload_to_azure_storage(blob_service_client, "sitemaps", blob_name, sitemap_content)

    return blob_url

def add_lastmod_to_sitemap(url_list, sitemap):
    # Load the XML file
    root = sitemap

    # Namespace used in the XML
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Extract URLs and lastmod values from the XML
    url_lastmod_map = {}
    for url_element in root.findall('ns:url', namespace):
        loc = url_element.find('ns:loc', namespace).text
        lastmod = url_element.find('ns:lastmod', namespace).text
        url_lastmod_map[loc] = lastmod


    # Create the dictionary containing the URLs and lastmod values
    result_dict = {url: url_lastmod_map.get(url, None) for url in url_list}

    # Print the result
    return result_dict
   
def upload_new_posts_to_cosmosdb(sitemap_url):
    # Read the sitemap from the URL
    new_sitemap = read_sitemap_from_url(sitemap_url)

    # remove the protocol from url
    blob_name = sitemap_url.split("//")[1]

    # Read the sitemap from Azure Storage
    old_sitemap = read_sitemap_from_azstorage(blob_name)

    # Find the differences between the two sitemaps
    new_urls = find_differences(new_sitemap, old_sitemap)

    # Add the lastmod values to the new URLs
    new_urls_with_lastmod = add_lastmod_to_sitemap(new_urls, new_sitemap)

    logger.info(f"Found {len(new_urls_with_lastmod)} new blog posts")

    blog = BlogPosts()
    for url, lastmod in new_urls_with_lastmod.items():
        blog.insert_blog_post(url, lastmod)

def process_sitemap(sitemap_uri):
    upload_new_posts_to_cosmosdb(sitemap_uri)
    blob_url = save_sitemap_file_to_azure_storage(sitemap_uri)
    logger.info(f"Saved sitemap to {blob_url}") 

if __name__ == "__main__":
    sitemap_uri = "https://meyerperin.org/sitemap.xml"
    process_sitemap(sitemap_uri)