from social_media import SocialMediaDocument, Bluesky, LinkedIn
import logging
from utils.cosmosdb import _get_container
from datetime import datetime, timezone
from typing import List

logger = logging.getLogger("tm-poster")
logger.setLevel(logging.DEBUG)


class SocialMediaPoster:
    def __init__(self):
        pass

    def _generate_document(
        self,
        text: str,
        after_utc: str = "2000-01-01T00:00:00Z",
        service: str = "Bluesky",
        image_url: str | None = None,
        img_file: str | None = None,
        url: str | None = None,
        url_title: str | None = None,
        hashtags: list[str] | None = None,
        emojis: list[str] | None = None,
    ) -> SocialMediaDocument:
        document = SocialMediaDocument(
            text=text,
            service=service,
            after_utc=after_utc,
            image_url=image_url,
            img_file=img_file,
            url=url,
            url_title=url_title,
            hashtags=hashtags,
            emojis=emojis,
        )
        return document

    def _queue_document(self, document: SocialMediaDocument):
        container = _get_container("posts", "post_documents")
        container.upsert_item(document.model_dump())

    def _post_document(
        self, document: SocialMediaDocument
    ) -> SocialMediaDocument | None:
        service = document.service

        if service == "Bluesky":
            bluesky = Bluesky()
            document = bluesky.post_document(document)

        if service == "LinkedIn":
            linkedin = LinkedIn()
            document = linkedin.post_document(document)

        container = _get_container("posts", "post_documents")
        container.upsert_item(document.model_dump())

        return document

    def generate_and_queue_document(
        self,
        text: str,
        after_utc: str = "2000-01-01T00:00:00Z",
        service: str = "Bluesky",
        image_url: str | None = None,
        img_file: str | None = None,
        url: str | None = None,
        url_title: str | None = None,
        hashtags: list[str] | None = None,
        emojis: list[str] | None = None,
    ) -> str:

        document = self._generate_document(
            text=text,
            service=service,
            after_utc=after_utc,
            image_url=image_url,
            img_file=img_file,
            url=url,
            url_title=url_title,
            hashtags=hashtags,
            emojis=emojis,
        )
        self._queue_document(document)
        return document.id

    def get_post_queue(self) -> List[SocialMediaDocument]:
        container = _get_container("posts", "post_documents")

        # get the current utc time
        utc_time_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        query = f"SELECT * FROM c WHERE (c.posted_utc = null) OR (NOT IS_DEFINED(c.posted_utc)) ORDER BY c.after_utc"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        return [SocialMediaDocument(**item) for item in items]

    def post_next_document(self) -> SocialMediaDocument | None:
        container = _get_container("posts", "post_documents")

        # get the current utc time
        utc_time_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        query = f"SELECT TOP 1 * FROM c WHERE (c.posted_utc = null AND c.after_utc < '{utc_time_now}') OR (NOT IS_DEFINED(c.posted_utc)) ORDER BY c.after_utc"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        if len(items) == 0:
            logger.info("No documents to post")
            return None
        return self._post_document(SocialMediaDocument(**items[0]))

    def post_with_id(self, id: str | None) -> SocialMediaDocument | None:
        if id is None:
            logger.warning("No id provided to post_with_id")
            return None
        
        container = _get_container("posts", "post_documents")
        query = f"SELECT * FROM c WHERE c.id = '{id}'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        if len(items) == 0:
            logger.info(f"No document with id {id}")
            return None
        return self._post_document(SocialMediaDocument(**items[0]))

    def get_post_details(self, id: str) -> SocialMediaDocument | None:
        container = _get_container("posts", "post_documents")
        query = f"SELECT * FROM c WHERE c.id = '{id}'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        if len(items) == 0:
            logger.info(f"No document with id {id}")
            return None
        return SocialMediaDocument(**items[0])

    def delete_post(self, id: str) -> bool:
        container = _get_container("posts", "post_documents")
        try:
            container.delete_item(id, partition_key=id)
            return True
        except Exception as e:
            logger.error(f"Error deleting post with id {id}: {e}")
            return False

    def upsert_post(self, document: SocialMediaDocument) -> bool:
        container = _get_container("posts", "post_documents")
        try:
            container.upsert_item(document.model_dump())
            return True
        except Exception as e:
            logger.error(f"Error upserting post with id {document.id}: {e}")
            return False