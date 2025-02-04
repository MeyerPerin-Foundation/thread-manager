import logging
from atproto import client_utils, Client
import requests

from . import app_config

logger = logging.getLogger("tm-bluesky")

class Bluesky:

    def __init__(self):
        self.client = Client()

    def post(self, text, image_url=None, img_file=None, hashtags=None, emojis=None, url=None, url_title=None):
        
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
            text_builder.tag(hashtag_text, hashtag)

        if url is not None:
            if url_title is not None:
                text_builder.link(f"\n{url_title}\n", url)
            else:
                text_builder.link(f"\n{url}\n", url)

        self.client.login(app_config.BSKY_USER, app_config.BSKY_APP_PWD)

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

        logger.info(f"Result of post_to_bluesky: {post_uri}")
        return "OK", 200
