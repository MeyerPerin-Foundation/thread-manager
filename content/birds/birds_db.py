from utils.cosmosdb import _get_container
from utils.cosmosdb import _get_setting
import random
import datetime
import logging

dblogger = logging.getLogger("tm-cosmosdb")

class BirdsDB:
    def __init__(self):
        self.container = _get_container

    def insert_bird(self, media_id, created_at, postcard_id, species, blob_url):
        container = self.container("content", "bird_buddy")

        # try to get the item from the database
        query = f"SELECT * FROM c WHERE c.id = '{media_id}'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )

        if items:
            item = items[0]
            item["created_at"] = created_at
            item["postcard_id"] = postcard_id
            item["species"] = species
            item["blob_url"] = blob_url
        else:
            item = {
                "id": media_id,
                "created_at": created_at,
                "postcard_id": postcard_id,
                "species": species,
                "blob_url": blob_url,
            }

        container.upsert_item(item)

    def get_random_birdbuddy(self):
        container = self.container("content", "bird_buddy")
        query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted)"

        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        # get a random item from the list
        return random.choice(items)

    def get_latest_unposted_birds(self, max_items=12):
        container = self.container("content", "bird_buddy")
        query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted) ORDER BY c.created_at DESC "
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )

        # items is a list of N items
        # get up to max_items from the list (this garantees most recent items)
        N = len(items)
        if N > max_items:
            items = items[:max_items]

        return items

    def update_birdbuddy_posted(self, birdbuddy_dict):
        container = self.container("content", "bird_buddy")
        birdbuddy_dict["last_posted"] = datetime.datetime.now().isoformat()
        container.upsert_item(birdbuddy_dict)
        return birdbuddy_dict

    def count_birds(self):
        container = self.container("content", "bird_buddy")
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        all_birds = items[0]

        query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted)"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        unposted_birds = items[0]

        d = {"all_birds": all_birds, "unposted_birds": unposted_birds}

        return d

    def get_bird_description_voice_options(self):
        return _get_setting("bird_description_voice_options")

    def get_latest_bird_update(self):
        return _get_setting("latest_bird_update")

    def get_bird_list(self):
        container = self.container("content", "bird_buddy")
        # latest 20 items
        query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted) AND (NOT IS_DEFINED(c.hide) or NOT c.hide) ORDER BY c.created_at DESC"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        return items[:20]

    def get_bird(self, id: str):
        container = self.container("content", "bird_buddy")
        query = f"SELECT * FROM c WHERE c.id = '{id}'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        if items:
            return items[0]
        else:
            return None

    def update_bird(self, data: dict):
        container = self.container("content", "bird_buddy")

        try:
            container.upsert_item(data)
        except Exception as e:
            dblogger.error(f"Error updating bird {data['id']}: {e}")
            return False

    def set_latest_bird_update(self, latest_update_isoformat=None):
        if not latest_update_isoformat:
            latest_update_isoformat = datetime.datetime.now(datetime.UTC).isoformat()

        container = _get_container("control", "settings")
        query = "SELECT * FROM c WHERE c.id = 'v1'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )
        if items:
            item = items[0]
            item["latest_bird_update"] = latest_update_isoformat
        else:
            item = {"id": "v1", "latest_bird_update": latest_update_isoformat}
        container.upsert_item(item)
