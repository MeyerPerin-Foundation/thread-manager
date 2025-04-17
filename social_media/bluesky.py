from app_config import BSKY_APP_PWD, BSKY_USER
import logging
import requests
from atproto import client_utils, Client, models, IdResolver
from datetime import datetime, timezone, timedelta
from social_media.document import SocialMediaDocument, SocialMediaPostResult
from PIL import Image, ImageOps
from io import BytesIO
from utils.ai.ai import generate_image_alt_text

logger = logging.getLogger("tm-bluesky")
logger.setLevel(logging.DEBUG)

class Bluesky:
    def __init__(self):
        self.client = Client()
        self.client.login(BSKY_USER, BSKY_APP_PWD)

    def unfollow(self, handle: str) -> bool:
        # Unf7ollow the given handle
        try:
            self.client.unfollow(handle)
            return True
        except Exception as e:
            logger.error(f"Error unfollowing {handle}: {e}")
            return False

    def get_follower_count(self) -> int:
        profile = self.client.get_profile(BSKY_USER)
        return profile["followers_count"]

    def get_follows_list(self, limit=100) -> list:
        f = self.client.get_follows(BSKY_USER, limit=limit)
        cursor = None
        follows = []
        while True:
            fetched = self.client.app.bsky.graph.get_follows(params={'actor': BSKY_USER, 'cursor': cursor})
            follows = follows + fetched.follows
            if not fetched.cursor:
                break
            cursor = fetched.cursor
        return follows

    def get_profile_posts(self, handle: str, limit=10) -> list:
        # Get the profile posts for the given user
        try:
            profile_feed = self.client.get_author_feed(actor=handle, limit=limit)
            return profile_feed.feed
        except Exception as e:
            logger.error(f"Error getting profile posts for {handle}: {e}")
            return []

    def get_percent_reposts(self, handle: str) -> float:
        # Get the profile posts for the given user
        try:
            feed = self.get_profile_posts(handle, limit=20)
        except Exception as e:
            logger.error(f"Error getting profile posts for {handle}: {e}")
            return 0.0
        reposts = []
        for post in feed:
            if post.reason and post.reason.py_type == "app.bsky.feed.defs#reasonRepost":
                reposts.append(post)                        
        
        try:
            return len(reposts) / len(feed) * 100 if profile_feed.feed else 0.0
        except ZeroDivisionError:
            return 0.0

    def get_post_frequency(self, handle: str) -> bool:
        # Get the profile posts for the given user
        try:
            feed = self.get_profile_posts(handle, limit=20)
        except Exception as e:
            logger.error(f"Error getting profile posts for {handle}: {e}")
            return 0.0
        
        # check if the user has posted in the last 7 days
        for item in feed:
            # get the item.post.record.created_at and convert it from a string to a datetime object
            created_at = datetime.strptime(item.post.record.created_at[:19], "%Y-%m-%dT%H:%M:%S")
            # convert the created_at to UTC timezone
            created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at > datetime.now(timezone.utc) - timedelta(days=7):
                return True

        # check if the user posted at least four times in the last 30 days
        post_count = 0
        for item in feed:
            created_at = datetime.strptime(item.post.record.created_at[:19], "%Y-%m-%dT%H:%M:%S")
            # convert the created_at to UTC timezone
            created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at > datetime.now(timezone.utc) - timedelta(days=30):
                post_count += 1
                if post_count >= 4:
                    return True
        
        return False

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

    def downscale_to_box(self,
                        src: bytes,
                        box: tuple[int, int],
                        *,
                        keep_metadata: bool = True) -> Image.Image:
        """
        Down‑scales image bytes so that width ≤ box[0] and height ≤ box[1] using
        Lanczos resampling. Returns the resized PIL.Image.
        """
        img = Image.open(BytesIO(src))
        img = ImageOps.exif_transpose(img)  # auto-orient using EXIF

        img.thumbnail(box, Image.LANCZOS)

        if not keep_metadata:
            img_no_meta = Image.new(img.mode, img.size)
            img_no_meta.putdata(list(img.getdata()))
            img = img_no_meta

        return img

    def save_under_size(self,
                        img: Image.Image,
                        target_bytes: int,
                        min_q: int = 50,
                        max_q: int = 100,
                        step: int = 1,
                        subsampling: int = 2) -> bytes:
        """
        Save a PIL.Image to JPEG bytes with size ≤ target_bytes using binary search on quality.
        Returns the JPEG image bytes.
        """
        lo, hi, best = min_q, max_q, None

        while lo <= hi:
            q = (lo + hi) // 2
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=q,
                    optimize=True, progressive=True,
                    subsampling=subsampling)
            b = buf.tell()

            if b <= target_bytes:
                best = buf.getvalue()
                lo = q + step
            else:
                hi = q - step

        if best is None:
            raise ValueError("Cannot reach target even at minimum quality.")

        return best

    def post(
        self,
        text: str,
        image_urls: list[str] = None,
        image_alts: list[str] = None,
        hashtags: list[str] = None,
        urls: list[str] = None,
        url_titles: list[str] = None,
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
                for i in range(len(urls)):
                    text_builder.link(f"\n{url_titles[i]}\n", urls[i])

        # Check if there's an image
        if image_urls is not None:

            # get the first 4 images
            if len(image_urls) > 4:
                logger.info(f"Only posting the first 4 images of {len(image_urls)}")
                image_urls = image_urls[:4]
            
            image_data = []
            image_aspect_ratios = []
            
            # resize image to appropriate bsky constraints (1000000 bytes, 2048x2048 box)
            for url in image_urls:
                original_data = requests.get(url).content
                img_resized = self.downscale_to_box(original_data, (2048, 2048), keep_metadata=True)
                final_bytes = self.save_under_size(img_resized, 1_000_000)
                image_data.append(final_bytes)

                with Image.open(BytesIO(final_bytes)) as img:
                    image_aspect_ratios.append(models.AppBskyEmbedDefs.AspectRatio(height=img.height, width=img.width))

            image_alts = [generate_image_alt_text(image_urls[i]) for i in range(len(image_urls))]
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

    b.post("Testing hi-res image", image_urls=["https://threadmanager.blob.core.windows.net/users/lcvvIIfrcgy3oo8NKhjkLYJDZvHJKG0Nj3gerYEDsgQ/original_photography/2025_04_03_Fulshear/1ea2ee6e-98e2-513f-a8d8-ea2aef4f0233.jpg"])

    # follows = b.get_follows_list(limit=None)
    # for follow in follows:
    #     if b.get_post_frequency(follow.handle) == False:
    #         print(f"Unfollowing {follow.handle} with not enough posts")
    #         b.unfollow(follow.viewer.following)

        # repost_percentage = b.get_percent_reposts(follow.handle)
        # if repost_percentage > 66:
        #     try:
        #         print(f"Unfollowing {follow.handle} with {repost_percentage}% reposts")
        #         b.unfollow(follow.viewer.following)
        #     except Exception as e:
        #         print(f"Error unfollowing {follow.handle}: {e}")
        #     print(f"Unfollowed {follow.handle} with {repost_percentage}% reposts")
    
    # resolver = IdResolver()
    # did = resolver.handle.resolve("cautious-robot.bsky.social")
    # key = f"at://{did}"
    # print(f"Unfollowing {key}")
    # b.unfollow(key)
    # b.unfollow("at://did:plc:lg76krbsc3f2ajnqdp4t47e2/app.bsky.graph.follow/3llfr3vufe72p")