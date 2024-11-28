from azure.cosmos import CosmosClient
import app_config
import random
import datetime

def get_motd():
    # get current month and day in the format MMDD
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("post_of_the_day")

    month_day = datetime.datetime.now().strftime("%m%d")
    query = f"SELECT * FROM c WHERE c.day_month = '{month_day}'"
    
    # return the first item in the list
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if items:
        return items[0]
    else:
        return None


def check_user_in_db(user):
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("users")
    container = database.get_container_client("users")

    # Get the sub from the user
    sub = user.get("sub")

    if not sub:
        return False
    
    # Query to retrieve a specific record
    query = f"SELECT * FROM c WHERE c.sub = '{sub}'"

    # Fetching the record
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        return False
    else:
        return True    
    
def get_random_ungovernable():
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("ungovernable")

    query = "SELECT * FROM c"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def get_random_too_far():
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("gone_too_far")

    query = "SELECT * FROM c"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def get_random_birdbuddy():
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("bird_buddy")

    query = "SELECT * FROM c where NOT IS_DEFINED(c.last_posted)"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def update_birdbuddy_posted(birdbuddy_dict):
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("bird_buddy")

    birdbuddy_dict["last_posted"] = datetime.datetime.now().isoformat()
    container.upsert_item(birdbuddy_dict)
    return birdbuddy_dict

def insert_bird(media_id, created_at, postcard_id, species, blob_url):
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("bird_buddy")

    item = {
        "id": media_id,
        "created_at": created_at,
        "postcard_id": postcard_id,
        "species": species,
        "blob_url": blob_url
    }
    container.upsert_item(item)

def count_birds():
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client("content")
    container = database.get_container_client("bird_buddy")

    query = "SELECT VALUE COUNT(1) FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    all_birds = items[0]

    query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted)"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    unposted_birds = items[0]

    d = {
        "all_birds": all_birds,
        "unposted_birds": unposted_birds
    }

    return d