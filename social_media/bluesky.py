from app_config import BSKY_APP_PWD, BSKY_USER
import logging
import requests
from atproto import client_utils, Client
from datetime import datetime, timezone
from social_media.document import SocialMediaDocument, SocialMediaPostResult

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
        image_url = document.image_url
        img_file = document.img_file
        hashtags = document.hashtags
        emojis = document.emojis
        url = document.url
        url_title = document.url_title

        result = self.post(text, image_url, img_file, hashtags, emojis, url, url_title)

        document.posted_utc = result.posted_utc
        document.posted_uri = result.posted_uri
        document.result_message = result.result_message
        document.result_code = result.result_code

        return document

    def post(
        self,
        text,
        image_url=None,
        img_file=None,
        hashtags=None,
        emojis=None,
        url=None,
        url_title=None,
    ) -> SocialMediaPostResult:
        
        logger.info(f"Posting {text} to Bluesky")

        message = text

        if emojis is not None:
            for emoji in emojis:
                message += emoji

        text_builder = client_utils.TextBuilder()
        text_builder.text(message + "\n")

        if hashtags is None:
            hashtags = []

        for hashtag in hashtags:
            # if the hashtag does not start with a #, add it
            if not hashtag.startswith("#"):
                hashtag_text = "#" + hashtag
            text_builder.tag(hashtag_text + " ", hashtag)

        if url is not None:
            if url_title is not None:
                text_builder.link(f"\n{url_title}\n", url)
            else:
                text_builder.link(f"\n{url}\n", url)

        # Check if there's an image
        image_data = None
        if img_file is not None:
            with open(img_file, "rb") as image_file:
                image_data = image_file.read()

        if image_url is not None:
            image_data = requests.get(image_url).content

        if image_data is None:
            post = self.client.send_post(text_builder)
        else:
            post = self.client.send_image(text_builder, image=image_data, image_alt="")

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
