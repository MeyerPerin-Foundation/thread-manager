from .too_far_db import TooFarDB
from social_media import SocialMediaPoster, SocialMediaDocument
import logging

logger = logging.getLogger("tm-too-far")
logger.setLevel(logging.INFO)

class TooFarContent:

    def generate_too_far(self, service="Bluesky", after_utc = None) -> str | None:
        too_far = TooFarDB()
        too_far_dict = too_far.get_random_too_far()

        if not too_far_dict:
            logger.warning("No too far content found")
            return None

        # remove high unicode characters
        message = too_far_dict["title"]
        message = message.encode("ascii", "ignore").decode("ascii")

        p = SocialMediaPoster()
        id = p.generate_and_queue_document(text=message, service=service, hashtags=["GoneTooFar"], image_urls=[too_far_dict["blob_url"]], after_utc=after_utc)
        if not id:
            return None
        too_far_dict["title"] = message
        too_far.update_too_far_posted(too_far_dict)


    def post_too_far(self) -> SocialMediaDocument | None:
        p = SocialMediaPoster()
        id = self.generate_too_far()
        return p.post_with_id(id)
        

    def count_too_far(self) -> int:
        too_far = TooFarDB()
        return too_far.count_too_far()  
