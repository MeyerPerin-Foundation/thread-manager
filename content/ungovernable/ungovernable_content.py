from social_media import SocialMediaPoster, SocialMediaDocument
from .ungovernable_db import UngovernableDB
import logging

logger = logging.getLogger("tm-ungov")
logger.setLevel(logging.INFO)

class UngovernableContent:

    def queue_ungovernable(self, after_utc = None) -> str | None:
        ungov = UngovernableDB()
        ungovernable_dict = ungov.get_random_ungovernable()

        if not ungovernable_dict:
            logger.warning("No ungovernable content found")
            return None

        message = ungovernable_dict["title"]

        # remove high unicode characters
        message = message.encode("ascii", "ignore").decode("ascii")

        p = SocialMediaPoster()
        id = p.generate_and_queue_document(text=message, hashtags=["BecomeUngovernable"], image_urls=[ungovernable_dict["blob_url"]], after_utc=after_utc)
        if not id:
            return None
            
        ungovernable_dict["title"] = message
        ungov.update_ungovernable_posted(ungovernable_dict)
        return id

    def post_ungovernable(self) -> SocialMediaDocument | None:
        p = SocialMediaPoster()
        id = self.queue_ungovernable()
        return p.post_with_id(id)

    def count_ungovernable(self):
        ungov = UngovernableDB()
        return ungov.count_ungovernable()

