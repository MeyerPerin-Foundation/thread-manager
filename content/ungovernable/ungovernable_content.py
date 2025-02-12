from social_media import SocialMediaPoster, SocialMediaDocument
from .ungovernable_db import UngovernableDB
import logging

logger = logging.getLogger("tm-ungov")
logger.setLevel(logging.INFO)

class UngovernableContent:

    def post_ungovernable(self) -> SocialMediaDocument | None:
        ungov = UngovernableDB()
        ungovernable_dict = ungov.get_random_ungovernable()

        if not ungovernable_dict:
            print("No ungovernable content found")
            return None

        message = ungovernable_dict["title"]

        # remove high unicode characters
        message = message.encode("ascii", "ignore").decode("ascii")

        p = SocialMediaPoster()
        
        id = p.generate_and_queue_document(text=message, hashtags=["BecomeUngovernable"], image_url=ungovernable_dict["blob_url"])
        ungovernable_dict["title"] = message
        ungov.update_ungovernable_posted(ungovernable_dict)
        return p.post_with_id(id)

    def count_ungovernable(self):
        ungov = UngovernableDB()
        return ungov.count_ungovernable()

