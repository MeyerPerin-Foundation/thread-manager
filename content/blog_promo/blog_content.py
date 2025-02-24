import logging
from typing import List
from social_media import SocialMediaPoster, SocialMediaDocument
from .blog_reader import blog_li_summary, blog_bt_summary, blog_li_full_text


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
        title, image_url, bt_message = blog_bt_summary(blog_post_metadata["url"])
        p = SocialMediaPoster()
        id = p.generate_and_queue_document(
            text=bt_message,
            hashtags=["BlogPost"],
            urls=[blog_post_metadata["url"]],
            url_titles=[title],
            after_utc=after_utc,
        )
        ids.append(id)

        title, image_url, linkedin_message = blog_li_full_text(blog_post_metadata["url"])
        if len(linkedin_message) > 2800:
            linkedin_message = linkedin_message[:2800]
            linkedin_message += "\n\n[continued in blog post below]\n\n"

        linkedin_message += f"\n\nRead the full blog post here: {blog_post_metadata['url']}"

        id = p.generate_and_queue_document(
            service="LinkedIn",
            text=linkedin_message,
            hashtags=["BlogPost"],
            urls=[blog_post_metadata["url"]],
            url_titles=[title],
            image_url=image_url,
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


if __name__ == "__main__":
    url =  "https://meyerperin.org/posts/2025-02-05-all-cool-kids-using-uv.html"
    title, image_url, content = blog_li_full_text(url)
    print(title)
    print(image_url)
    print(content)
    