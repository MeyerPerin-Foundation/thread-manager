import logging
from social_media import SocialMediaPoster, SocialMediaDocument
from utils.cosmosdb import BlogPostsDB
from content.blog_promo.blog_reader import blog_bt_summary, blog_li_summary

logger = logging.getLogger("tm-blog-promo")
logger.setLevel(logging.INFO)


class BlogPromoContent:

    # TODO: break by service, move decision up
    def post_blog_promo(self) -> SocialMediaDocument | None:

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
            url=blog_post_metadata["url"],
            url_title="Read blog post",
        )
        p.post_with_id(id)

        linkedin_message = blog_li_summary(blog_post_metadata["url"])
        id = p.generate_and_queue_document(
            service="LinkedIn",
            text=linkedin_message,
            hashtags=["BlogPost"],
            url=blog_post_metadata["url"],
        )
        blog.update_blog_posted(blog_post_metadata)

        return p.post_with_id(id)
