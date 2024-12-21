from ._dbutils import _get_container
import datetime


class Dashboard:
    def __init__(self):
        self.container = _get_container

    def latest_dashboard_data(self):
        # select the record for the current date
        query = "SELECT * FROM c ORDER BY c.id DESC"
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )

        if items:
            return items[0]
        else:
            return None

    def update_dashboard(self, d: dict):
        container = _get_container("control", "daily_dashboard")

        # get the date in UTC in the format YYYYMMDD
        date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")

        # select the record for the current date
        query = f"SELECT * FROM c WHERE c.id = '{date}'"
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )

        if items:
            # update the existing record
            item = items[0]
            item.update(d)
            container.upsert_item(item)
        else:
            # create a new record
            d["id"] = date
            container.upsert_item(d)

        return d
