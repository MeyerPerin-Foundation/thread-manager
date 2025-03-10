from app_config import BSKY_APP_PWD, BSKY_USER
import logging
import requests
from atproto import client_utils, Client, models
from datetime import datetime, timezone
from social_media.document import SocialMediaDocument, SocialMediaPostResult
from PIL import Image
from io import BytesIO

logger = logging.getLogger("tm-bluesky")
logger.setLevel(logging.DEBUG)

class Bluesky:
    def __init__(self):
        self.client = Client()
        self.client.login(BSKY_USER, BSKY_APP_PWD)


    def get_follower_count(self) -> int:
        profile = self.client.get_profile(BSKY_USER)
        return profile["followers_count"]


    def post_document(self, document: SocialMediaDocument) -> SocialMediaDocument:
        # extract the components of the document
        text = document.text
        image_urls = document.image_urls
        hashtags = document.hashtags
        urls = document.urls
        url_titles = document.url_titles

        result = self.post(text, 
            image_urls=image_urls, 
            urls=urls, 
            url_titles=url_titles,
            hashtags=hashtags)

        document.posted_utc = result.posted_utc
        document.posted_uri = result.posted_uri
        document.result_message = result.result_message
        document.result_code = result.result_code

        return document

    def post(
        self,
        text,
        image_urls=None,
        image_alts=None,
        hashtags=None,
        urls=None,
        url_titles=None,
    ) -> SocialMediaPostResult:
        
        logger.info(f"Posting {text} to Bluesky")

        message = text
        text_builder = client_utils.TextBuilder()
        text_builder.text(message + "\n")

        if hashtags is None:
            hashtags = []

        for hashtag in hashtags:
            # if the hashtag does not start with a #, add it
            if not hashtag.startswith("#"):
                hashtag_text = "#" + hashtag
            text_builder.tag(hashtag_text + " ", hashtag)

        if urls is not None:
            if url_titles is not None:
                text_builder.link(f"\n{url_titles[0]}\n", urls[0])

        # Check if there's an image
        if image_urls is not None:

            # get the first 4 images
            if len(image_urls) > 4:
                logger.info(f"Only posting the first 4 images of {len(image_urls)}")
                image_urls = image_urls[:4]
            image_data = [requests.get(image_url).content for image_url in image_urls]
            image_aspect_ratios = []
            for data in image_data:
                with Image.open(BytesIO(data)) as img:
                    image_aspect_ratios.append(models.AppBskyEmbedDefs.AspectRatio(height=img.height, width=img.width))
            image_alts = [image_alts[i] if image_alts else "" for i in range(len(image_urls))]
            post = self.client.send_images(text_builder, images=image_data, image_alts=image_alts, image_aspect_ratios=image_aspect_ratios)
        else:
            post = self.client.send_post(text_builder)

        post_uri = post.uri

        # get the current UTC time
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        post_result = SocialMediaPostResult(
            result_message="OK",
            result_code=200,
            posted_uri=post_uri,
            posted_utc=utc_now,
        )

        return post_result

if __name__ == "__main__":
    b = Bluesky()
    d = SocialMediaDocument(
        text="Trying to have fun with the API and multiple images",
        image_urls=[
            "https://threadmanager.blob.core.windows.net/become-ungovernable/1708107164.jpg",
            "https://threadmanager.blob.core.windows.net/become-ungovernable/1707882387.jpg"
        ],
    )
    b.post_document(d)