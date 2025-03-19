from utils.cosmosdb import _get_container
import random
from datetime import datetime, timezone, timedelta

class TooFarDB:
    def __init__(self):
        self.container = _get_container("content", "gone_too_far")

    def count_too_far(self):
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )
        all_too_far = items[0]

        
        waiting_period = datetime.now(timezone.utc) - timedelta(days=180)
        waiting_period = waiting_period.isoformat()
    
        query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted) OR c.last_posted < @waiting_period"
        parameters = [{"name": "@waiting_period", "value": waiting_period}]

        items = list(
            self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True)
        )
        unposted_too_far = items[0]

        d = {"all_too_far": all_too_far, "unposted_too_far": unposted_too_far}

        return d

    def update_too_far_posted(self, too_far_dict):
        too_far_dict["last_posted"] = datetime.now().isoformat()
        self.container.upsert_item(too_far_dict)
        return too_far_dict

    def get_random_too_far(self):

        # get the date and time three months ago in UTC
        waiting_period = datetime.now(timezone.utc) - timedelta(days=180)
        waiting_period = waiting_period.isoformat()
    
        query = "SELECT * FROM c WHERE NOT IS_DEFINED(c.last_posted) OR c.last_posted < @waiting_period"
        parameters = [{"name": "@waiting_period", "value": waiting_period}]


        items = list(
            self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True)
        )
        # get a random item from the list
        return random.choice(items)
