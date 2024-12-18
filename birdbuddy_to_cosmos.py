import datetime
from birdbuddy.client import BirdBuddy
from io import BytesIO
from azure.storage.blob import BlobServiceClient
import cosmosdb 
import requests
import app_config
import ai
import logging

logger = logging.getLogger("tm-birdbuddy-loader")

def upload_to_azure_storage(blob_service_client, container_name, blob_name, data):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)
    blob_url = blob_client.url
    return blob_url

async def fetch_new_feed_items(api_client, since):
    feed_response = await api_client.refresh_feed(since=since)
    # Extract edges (feed items) and add to the collection
    return feed_response

async def get_media_list(api_client, since):
    edges = await fetch_new_feed_items(api_client, since)

    media_list = []

    for edge in edges:
        feeder_name = ""
        typename = edge.get('__typename')
        node_id = edge.get('id')
        media_collection = None
        errors = 0

        if typename == "FeedItemNewPostcard":
            try:
                sighting = await api_client.sighting_from_postcard(node_id) 
                species = sighting.report.sightings[0].species.name
                feeder = sighting.get('feeder', {})
                feeder_name = feeder.get('name')
                feeder_location = feeder.get('location')

                if feeder_name == "MeyerPerin Backyard" or feeder_name == "MeyerPerin Birdbuddy Pro" or feeder_name == "MeyerPerin Front Yard":
                    media_collection = sighting.medias
                    encounter_id = sighting.postcard_id

                if media_collection is None:
                    continue

                media_items = [{'encounter_id': encounter_id, 
                                'id': item['id'], 
                                'date_created': item['createdAt'], 
                                'species': species,
                                'feeder_name': feeder_name,
                                'location': feeder_location,
                                'media_type': item['__typename'], 
                                'image_url': item['contentUrl']} for item in media_collection if item['__typename'] == 'MediaImage' or item['__typename'] == 'MediaVideo']
                
                species_to_ignore = ['Unknown', 'Mystery Visitor', 'Common Grackle', 'Dark-eyed Junco']
                # if species is not None, and does not contain names in list of species to ignore, add to media_list
                if species and species not in species_to_ignore:              
                    media_list.extend(media_items)
                else:
                    logger.info(f"Skipping postcard {node_id} with species {species}")

            except Exception as e:
                logger.error(f"Error processing postcard {node_id}: {e}")
                errors = errors + 1
    
    return media_list

async def update_birds(since = None):

    if since is None:
        since = datetime.datetime.now() - datetime.timedelta(hours=25)
    
    logger.info(f"Updating birds captured by Birdbuddy since {since}")

    blob_service_client = BlobServiceClient.from_connection_string(app_config.STORAGE_CONNECTION_STRING)
    bb = BirdBuddy(app_config.BIRD_BUDDY_USER, app_config.BIRD_BUDDY_PASSWORD)
    media_list = await get_media_list(bb, since)

    # number of items in the media_list
    N = len(media_list)
    i = 0

    logger.info(f"Processing {N} bird items")

    # insert each item from media_list into cosmosdb
    for item in media_list:
        i += 1
        logger.info(f"Processing item {i} of {N}")
        uri = item['image_url']

        # upload all videos, but check images with OpenAI first
        if item['media_type'] == 'MediaImage':
            # if it's not a good bird, just skip it
            if not ai.good_birb(uri):
                continue
        
        logger.info("This is a good bird. Saving to Azure Storage and Cosmos DB.")
        
        # otherwise,  let's save it
        response = requests.get(uri)
        response.raise_for_status()
        data = BytesIO(response.content)

        if item['media_type'] == 'MediaImage':
            blob_name = f"{item['id']}.jpg"
        elif item['media_type'] == 'MediaVideo':
            blob_name = f"{item['id']}.mp4"

        # Upload to Azure Storage
        blob_url = upload_to_azure_storage(blob_service_client, "bird-buddy", blob_name, data.getvalue())

        # Save to Cosmos DB
        if blob_url:
            cosmosdb.insert_bird(media_id=item['id'], created_at = item['date_created'], postcard_id = item['encounter_id'], species = item['species'], blob_url=blob_url)


if __name__ == "__main__":
    import asyncio

    now = datetime.datetime.now(datetime.UTC)
    since = now - datetime.timedelta(hours=2, minutes=31)
    asyncio.run(update_birds(since.isoformat()))