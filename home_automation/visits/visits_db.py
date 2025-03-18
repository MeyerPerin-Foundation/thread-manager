import uuid
from utils.cosmosdb import _get_container


class VisitsDB:
    def __init__(self):
        # noop
        pass

    def update_dogtopia_visits(self, date: str, visits: int):
        container = _get_container("content", "dogtopia_visits")

        if visits >= 0:
            type = "deposit"
        else:
            type = "withdrawal"

        # build the id record
        id = f"{date}-{type}"

        item = {"id": id, "date": date, "type": type, "visits": visits}
        container.upsert_item(item)

    def insert_visit(self, date: str, person: str, location: str):
        container = _get_container("content", "visits")

        id = uuid.uuid4().hex
        item = {"id": id, "date": date, "location": location, "person": person}
        container.upsert_item(item)
    
    def current_balance(self, date: str) -> int:
        container = _get_container("content", "dogtopia_visits")
        query = f"SELECT * FROM c WHERE c.date <= '{date}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        if len(items) == 0:
            return 0

        balance = 0
        for item in items:
                balance += item["visits"]

        balance = int(balance)
        return balance
        