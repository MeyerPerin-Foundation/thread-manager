
import random
import logging
from .birds_db import BirdsDB
from social_media import SocialMediaPoster
import utils.ai.ai as ai

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