from mpfutils.cosmosdb import CosmosDBContainer
from mpfutils.azstorage import AzsContainerClient
import app_config
import uuid
from datetime import datetime, timezone, timedelta
import logging
import random
from social_media import SocialMediaPoster

logger = logging.getLogger("tm-folder-content")
if app_config.RUNNING_LOCALLY:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

class FolderContent:
    def __init__(self):
        self.storage = AzsContainerClient(container_name="users")
        self.db = CosmosDBContainer("content", "themed_folders")
        self.subscription_id = app_config.THREAD_MANAGER_SUBSCRIPTION_ID
        self.poster = SocialMediaPoster()

    def sync_folders_and_cosmos(self):
        prefix = f"{self.subscription_id}/themed_folders/"
        blobs = self.storage.list_blobs(prefix=self.subscription_id)
        folder_config = self.get_folder_config()

        for blob in blobs:
            # cut off the prefix
            blob_name = blob.name[len(prefix):]
            folder_name, file_name = blob_name.split("/", 1)
            blob_url = self.storage.get_blob_url(blob.name)

            text = folder_config[folder_name]["text"]
            hashtags = [folder_config[folder_name]["hashtag"]]
            id = str(uuid.uuid5(uuid.NAMESPACE_DNS, blob.name))

            d = {
                "id": id,
                "text": text,
                "hashtags": hashtags,
                "file_name": file_name,
                "subscription_id": self.subscription_id,
                "folder_name": folder_name,
                "blob_url": blob_url,
                "last_modified": blob.last_modified.isoformat(),
                "last_edited": blob.last_modified.isoformat(),
            }

            # check if the item already exists in the database
            existing_item = self.db.get_item(id, partition_key=self.subscription_id)

            if existing_item:
                # update the existing item if it has changed after the last modified date
                if d["last_modified"] > existing_item["last_edited"]:
                    logger.debug(f"Updating item {id} in the database")
                    self.db.upsert_item(d)
            else:
                # insert the new item into the database
                logger.debug(f"Inserting new item {id} into the database")
                self.db.upsert_item(d)

    def get_random_post(self, days_ago: int = 180) -> dict:
        """
        Returns a random post from the database.
        """
        if days_ago > 0:
            date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            date_str = date.isoformat()
            query = f"SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted) OR c.last_posted < '{date_str}'"
        else:
            query = "SELECT * FROM c"

        items = self.db.run_query(query)

        # pick a random item from the list
        item = random.choice(items)
        return item

    def get_folder_config(self) -> dict:
        """
        Returns the folder configuration from the database.
        """
        settings_db = CosmosDBContainer("control", "settings")
        settings = settings_db.get_item("v1")
        d = {}
        if not settings:
            settings = None
            raise ValueError("Settings not found in the database")
        else:
            d = settings.get("themed_folder_config")
            logger.debug(f"Settings found in the database\n{d}")

        if not d:
            raise ValueError("Themed folder config not found in the database")

        return d

    def queue_post(
        self, 
        service = "Bluesky",
        after_utc: str = "2000-01-01T00:00:00Z",
        days_ago: int = 180,
    ) -> str | None:
        """
        Queues a post to the specified service.
        """
        # get a random post from the database
        item = self.get_random_post(days_ago=days_ago)

        # queue the post
        id = self.poster.generate_and_queue_document(
            text=item["text"],
            after_utc=after_utc,
            service=service,
            image_urls=[item["blob_url"]],
            hashtags=item["hashtags"],
        )

        item["last_posted"] = datetime.now(timezone.utc).isoformat()
        self.db.upsert_item(item)
        return id

def sync_last_posted():
    db_folders = CosmosDBContainer("content", "themed_folders")
    db_too_far = CosmosDBContainer("content", "gone_too_far")
    db_ungovernable = CosmosDBContainer("content", "ungovernable")
    
    query = "SELECT * FROM c WHERE c.subscription_id = @subscription_id"
    params = [{"name": "@subscription_id", "value": app_config.THREAD_MANAGER_SUBSCRIPTION_ID}]
    items = db_folders.run_query(query, parameters=params)

    for item in items:
        folder_name = item["folder_name"]
        id = item["file_name"].split(".")[0]
        last_posted = None
        if folder_name == "become_ungovernable":
            existing_item = db_ungovernable.get_item(id)
            if existing_item:
                last_posted = existing_item.get("last_posted")
        if folder_name == "science_gone_too_far":
            existing_item = db_too_far.get_item(id)
            if existing_item:
                last_posted = existing_item.get("last_posted")
        if last_posted:
            item["last_posted"] = last_posted
            db_folders.upsert_item(item)
            logger.debug(f"Updated last_posted for {folder_name} {id} to {last_posted}")
             

if __name__ == "__main__":
    folder_content = FolderContent()
    id = folder_content.queue_post()
    print(id)
