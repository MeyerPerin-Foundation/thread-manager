from utils.cosmosdb import _get_container
import random
import datetime


class UngovernableDB:
    def __init__(self):
        self.container = _get_container("content", "ungovernable")

    def update_ungovernable_posted(self, ungovernable_dict):
        ungovernable_dict["last_posted"] = datetime.datetime.now().isoformat()
        self.container.upsert_item(ungovernable_dict)
        return ungovernable_dict

    def get_random_ungovernable(self):
        query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted)"

        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )

        # get a random item from the list
        return random.choice(items)

    def count_ungovernable(self):
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )
        all_ungovernable = items[0]

        query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted)"
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )
        unposted_ungovernable = items[0]

        d = {
            "all_ungovernable": all_ungovernable,
            "unposted_ungovernable": unposted_ungovernable,
        }

        return d
