from utils.cosmosdb import TooFarDB
from social_media import SocialMediaPoster, SocialMediaDocument

class TooFarContent:

    def post_too_far(self) -> SocialMediaDocument | None:
        too_far = TooFarDB()
        too_far_dict = too_far.get_random_too_far()

        if not too_far_dict:
            print("No too far content found")
            return None

        # remove high unicode characters
        message = too_far_dict["title"]
        message = message.encode("ascii", "ignore").decode("ascii")

        p = SocialMediaPoster()
        id = p.generate_and_queue_document(text=message, hashtags=["GoneTooFar"], image_url=too_far_dict["blob_url"])
        too_far_dict["title"] = message
        too_far.update_too_far_posted(too_far_dict)
        d = p.post_with_id(id)

        return d
