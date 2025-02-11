from azure.cosmos import CosmosClient
import app_config
import uuid
import datetime
import logging

dblogger = logging.getLogger("tm-cosmosdb")

def _get_container(database_name, container_name):
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)
    return container


def _get_setting(setting_name: str):
    container = _get_container("control", "settings")
    query = "SELECT * FROM c WHERE c.id = 'v1'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if items:
        return items[0].get(setting_name)
    else:
        return None


def _insert_test_record(data: dict):
    container = _get_container("control", "tests")

    if "id" not in data:
        data["id"] = uuid.uuid4().hex

    if "created_at" not in data:
        data["created_at_utc"] = datetime.datetime.now().isoformat()

    container.upsert_item(data)
