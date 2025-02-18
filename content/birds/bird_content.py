from utils.azstorage.azs_client import AzureStorageClient
from utils.cosmosdb import _get_setting
from io import BytesIO
import requests
import app_config
import random
import logging
from .birds_db import BirdsDB
from social_media import SocialMediaPoster
import utils.ai.ai as ai
from birdbuddy.client import BirdBuddy
import asyncio

logger = logging.getLogger("tm-birds")
logger.setLevel(logging.INFO)

class BirdContent:

    def generate_bird_caption(self, voices, blob_url, species, created_at, location) -> str:
        # Choose a random voice based on the weights
        weights = [voice["weight"] for voice in voices]
        voice = random.choices(voices, weights, k=1)[0]["voice"]

        # get the caption for the bird picture
        caption = ai.generate_caption_for_bird_picture(
            blob_url, species, created_at, location, voice
        )

        # if the message is in quotes, remove the quotes
        if caption.startswith('"') and caption.endswith('"'):
            caption = caption[1:-1]

        caption = f'As {voice}: "{caption}"'

        return caption

    def generate_birdbuddy_post(self, n_choices: int = 4, n_latest: int = 20, after_utc=None) -> str | None:
        birds = BirdsDB()
        latest_birds = birds.get_latest_unposted_birds(n_latest)

        n_birds = len(latest_birds)
        # from the list of items, get four random items
        
        if n_birds > n_choices:
            birdbuddy_list = random.sample(latest_birds, n_choices)
        else:
            birdbuddy_list = latest_birds


        if not birdbuddy_list:
            logger.info("No Bird Buddy content found")
            return None

        # create a list with the image urls
        image_url_list = [birdbuddy_dict["blob_url"] for birdbuddy_dict in birdbuddy_list]
        best_image = ai.choose_best_bird_image(image_url_list)

        # get the birdbuddy_dict for the best image
        birdbuddy_dict = next(
            (item for item in birdbuddy_list if item["blob_url"] == best_image), None
        )

        species = birdbuddy_dict.get("species", None)
        blob_url = birdbuddy_dict.get("blob_url", None)
        created_at = birdbuddy_dict.get("created_at", None)
        
        # feeder_name = birdbuddy_dict.get("feeder_name", None)
        location = birdbuddy_dict.get("location", "Fulshear,  Texas")
        
        # Create a dictionary with voice options and weights and choose a random one.
        voices = birds.get_bird_description_voice_options()

        caption = self.generate_bird_caption(voices, blob_url, species, created_at, location)
        while len(caption) > 275:
            logger.info(f"Caption too long: {len(caption)} characters, regenerating.")
            caption = self.generate_bird_caption(voices, blob_url, species, created_at, location)    
    
        p = SocialMediaPoster()
        id = p.generate_and_queue_document(
            text=f"{caption}",
            image_url=blob_url,
            hashtags=["birds"],
            emojis=["🪶"],
            url="https://t.ly/birdb",
            url_title="📷: Birdbuddy",
            after_utc=after_utc,
        )
        if not id:
            return None

        birds.update_birdbuddy_posted(birdbuddy_dict)
        return id


    def post_birdbuddy_picture(self, n_choices: int = 4, n_latest: int = 20) -> SocialMediaPoster | None:
        p = SocialMediaPoster()
        id = self.generate_birdbuddy_post(n_choices, n_latest)
        return p.post_with_id(id)

    def count_birds(self):
        birds = BirdsDB()
        return birds.count_birds()

    def upload_birds(self, since=None):
        return self.update_birds(since=since)

    def get_latest_bird_update(self):
        birds = BirdsDB()
        return birds.get_latest_bird_update()

    def set_latest_bird_update(self, last_update):
        birds = BirdsDB()
        return birds.set_latest_bird_update(last_update)


    def fetch_new_feed_items(self, api_client, since):
        feed_response = asyncio.run(api_client.refresh_feed(since=since))
        # Extract edges (feed items) and add to the collection
        return feed_response

    def get_media_list(self, api_client, since):
        edges = self.fetch_new_feed_items(api_client, since)

        media_list = []

        for edge in edges:
            feeder_name = ""
            typename = edge.get('__typename')
            node_id = edge.get('id')
            media_collection = None
            errors = 0

            if node_id in ['fa45e52e-fe57-47f4-86ae-d09816b1772f', 
                        '0aee2c1e-8219-4433-9da0-3580c0398d76',
                        'b43b120c-110c-48fe-9a77-6a7b305c611f',
                        '765e01b7-6ea9-4319-8bc8-915c5c38601c',
                        '59271c4c-68ef-4331-9819-02b57ce60560',
                        ]:
                logger.info(f"Skipping postcard {node_id} as it causes Birdbuddy server errors.")
                continue
            

            if typename == "FeedItemNewPostcard":
                try:
                    sighting = asyncio.run(api_client.sighting_from_postcard(node_id))
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
                    
                    species_to_ignore = _get_setting("species_to_ignore")
                    # if species is not None, and does not contain names in list of species to ignore, add to media_list
                    if species and species not in species_to_ignore:              
                        media_list.extend(media_items)
                    else:
                        logger.info(f"Skipping postcard {node_id} with species {species}")

                except Exception as e:
                    logger.error(f"Error processing postcard {node_id}: {e}")
                    errors = errors + 1
        
        return media_list

    def update_birds(self, since = None):

        if since is None:
            since = datetime.datetime.now() - datetime.timedelta(hours=25)
        
        logger.info(f"Updating birds captured by Birdbuddy since {since}")

        bb = BirdBuddy(app_config.BIRD_BUDDY_USER, app_config.BIRD_BUDDY_PASSWORD)
        media_list = self.get_media_list(bb, since)

        # number of items in the media_list
        N = len(media_list)
        i = 0

        logger.info(f"Processing {N} bird items")

        # insert each item from media_list into cosmosdb
        for item in media_list:
            i += 1
            logger.info(f"Processing item {i} of {N}")
            uri = item['image_url']

            # TODO: upload all videos, but check images with OpenAI first
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
            azsc = AzureStorageClient()
            blob_url = azsc.upload_blob("bird-buddy", blob_name, data.getvalue())

            birds = BirdsDB()
            # Save to Cosmos DB
            if blob_url:
                birds.insert_bird(media_id=item['id'], created_at = item['date_created'], postcard_id = item['encounter_id'], species = item['species'], blob_url=blob_url)

        logger.info("Finished processing bird items")