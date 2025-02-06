from ._dbutils import _get_container
import datetime


class MessageOfTheDayDB:
    def __init__(self):
        self.container = _get_container("content", "post_of_the_day")

    def get_motd(self):
        month_day = datetime.datetime.now().strftime("%m%d")
        query = f"SELECT * FROM c WHERE c.day_month = '{month_day}'"

        # return the first item in the list
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )
        if items:
            return items[0]
        else:
            return None
