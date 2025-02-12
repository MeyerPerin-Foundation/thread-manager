from .too_far_db import TooFarDB
from social_media import SocialMediaPoster, SocialMediaDocument
import logging

logger = logging.getLogger("tm-too-far")
logger.setLevel(logging.INFO)

class TooFarContent:

    def generate_too_far(self, after_utc = None) -> str | None:
        too_far = TooFarDB()
        too_far_dict = too_far.get_random_too_far()

        if not too_far_dict:
            logger.warning("No too far content found")
            return None

        # remove high unicode characters
        message = too_far_dict["title"]
        message = message.encode("ascii", "ignore").decode("ascii")

        p = SocialMediaPoster()
        id = p.generate_and_queue_document(text=message, hashtags=["GoneTooFar"], image_url=too_far_dict["blob_url"], after_utc=after_utc)
        too_far_dict["title"] = message
        too_far.update_too_far_posted(too_far_dict)


    def post_too_far(self) -> SocialMediaDocument | None:
        p = SocialMediaPoster()
        id = self.generate_too_far()
        return p.post_with_id(id)

