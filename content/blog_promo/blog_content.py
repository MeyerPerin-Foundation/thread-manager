import logging
from typing import List
from social_media import SocialMediaPoster, SocialMediaDocument
from content.blog_promo.blog_posts_db import BlogPostsDB
from content.blog_promo.blog_reader import blog_bt_summary, blog_li_summary

logger = logging.getLogger("tm-blog-promo")
logger.setLevel(logging.INFO)


class BlogPromoContent:

    def generate_blog_promo(self, after_utc = None) -> List[str] | None:
        
        ids = []
        blog = BlogPostsDB()
        blog_post_metadata = blog.get_latest_blog_post()

        if not blog_post_metadata:
            logger.info("No blog promo content found")
            return None

        # Different promo for LinkedIn and Threads/Bluesky
        bt_message = blog_bt_summary(blog_post_metadata["url"])
        p = SocialMediaPoster()
        id = p.generate_and_queue_document(
            text=bt_message,
            hashtags=["BlogPost"],
            urls=[blog_post_metadata["url"]],
            url_titles=["Read blog post"],
            after_utc=after_utc,
        )
        ids.append(id)

        linkedin_message = blog_li_summary(blog_post_metadata["url"])
        id = p.generate_and_queue_document(
            service="LinkedIn",
            text=linkedin_message,
            hashtags=["BlogPost"],
            urls=[blog_post_metadata["url"]],
            after_utc=after_utc,
        )
        ids.append(id)
        if not ids:
            return None
        blog.update_blog_posted(blog_post_metadata)
        return ids


    def post_blog_promo(self) -> SocialMediaDocument | None:
        p = SocialMediaPoster()
        ids = self.generate_blog_promo()
        if not ids:
            return None
        for id in ids:
            d = p.post_with_id(id)

        # return the last document posted
        return d
