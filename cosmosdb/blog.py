from ._dbutils import _get_container
import datetime


class BlogPosts:
    def __init__(self):
        self.container = _get_container("content", "blog_posts")

    def get_latest_blog_post(self):
        query = "SELECT TOP 1 * FROM c WHERE NOT IS_DEFINED(c.last_posted) ORDER BY c.lastmod DESC"

        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )
        if items:
            return items[0]
        else:
            return None

    def update_blog_posted(self, blog_post_dict):
        blog_post_dict["last_posted"] = datetime.datetime.now().isoformat()
        self.container.upsert_item(blog_post_dict)
        return blog_post_dict

    def insert_blog_post(self, url, lastmod):
        item = {"id": url.replace("/", "|"), "url": url, "lastmod": lastmod}
        self.container.upsert_item(item)
