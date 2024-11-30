from azure.cosmos import CosmosClient
import app_config
import random
import datetime
import uuid

def _get_container(database_name, container_name):
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)
    return container

def get_motd():
    # get current month and day in the format MMDD
    container = _get_container("content", "post_of_the_day")

    month_day = datetime.datetime.now().strftime("%m%d")
    query = f"SELECT * FROM c WHERE c.day_month = '{month_day}'"
    
    # return the first item in the list
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if items:
        return items[0]
    else:
        return None


def check_user_in_db(user):
    container = _get_container("users", "users")

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
    container = _get_container("content", "ungovernable")
    query = "SELECT * FROM c where NOT IS_DEFINED(c.last_posted)"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def get_random_too_far():
    container = _get_container("content", "gone_too_far")
    query = "SELECT * FROM c where NOT IS_DEFINED(c.last_posted)"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def get_random_birdbuddy():
    container = _get_container("content", "bird_buddy")
    query = "SELECT * FROM c where NOT IS_DEFINED(c.last_posted)"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    # get a random item from the list
    return random.choice(items)

def get_latest_blog_post():
    container = _get_container("content", "blog_posts")
    query = "SELECT TOP 1 * FROM c where NOT IS_DEFINED(c.last_posted) ORDER BY c.lastmod DESC"
    
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if items:
        return items[0]
    else:
        return None

def update_birdbuddy_posted(birdbuddy_dict):
    container = _get_container("content", "bird_buddy")
    birdbuddy_dict["last_posted"] = datetime.datetime.now().isoformat()
    container.upsert_item(birdbuddy_dict)
    return birdbuddy_dict

def update_too_far_posted(too_far_dict):
    container = _get_container("content", "gone_too_far")
    too_far_dict["last_posted"] = datetime.datetime.now().isoformat()
    container.upsert_item(too_far_dict)
    return too_far_dict

def update_ungovernable_posted(ungovernable_dict):
    container = _get_container("content", "ungovernable")
    ungovernable_dict["last_posted"] = datetime.datetime.now().isoformat()
    container.upsert_item(ungovernable_dict)
    return ungovernable_dict

def update_blog_posted(blog_post_dict):
    container = _get_container("content", "blog_posts")
    blog_post_dict["last_posted"] = datetime.datetime.now().isoformat()
    container.upsert_item(blog_post_dict)
    return blog_post_dict

def insert_bird(media_id, created_at, postcard_id, species, blob_url):
    container = _get_container("content", "bird_buddy")
    item = {
        "id": media_id,
        "created_at": created_at,
        "postcard_id": postcard_id,
        "species": species,
        "blob_url": blob_url
    }
    container.upsert_item(item)

def count_birds():
    container = _get_container("content", "bird_buddy")
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

def count_ungovernable():
    container = _get_container("content", "ungovernable")
    query = "SELECT VALUE COUNT(1) FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    all_ungovernable = items[0]

    query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted)"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    unposted_ungovernable = items[0]

    d = {
        "all_ungovernable": all_ungovernable,
        "unposted_ungovernable": unposted_ungovernable
    }

    return d

def count_too_far():
    container = _get_container("content", "gone_too_far")
    query = "SELECT VALUE COUNT(1) FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    all_too_far = items[0]

    query = "SELECT VALUE COUNT(1) FROM c where NOT IS_DEFINED(c.last_posted)"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    unposted_too_far = items[0]

    d = {
        "all_too_far": all_too_far,
        "unposted_too_far": unposted_too_far
    }

    return d

def get_prompt(function: str, version:int=None) -> str:
    container = _get_container("control", "prompts")
    
    if not version:
        # get the latest version
        query = f"SELECT * FROM c WHERE c.function = '{function}' ORDER BY c.version DESC"

    else:
        query = f"SELECT * FROM c WHERE c.function = '{function}' AND c.version = {version}"    

    records = list(container.query_items(query=query, enable_cross_partition_query=True))

    # if there are no records, raise an error
    if not records:
        raise ValueError(f"No prompt found for function {function} and version {version}")

    # else, get the record with the highest version
    record = records[0]
    prompt = record.get("prompt", None)

    if not prompt or prompt == "":
        raise ValueError(f"No prompt found for function {function} and version {version}")
    
    return prompt

def update_dashboard(d: dict):
    container = _get_container("control", "daily_dashboard")

    # get the date in UTC in the format YYYYMMDD
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")

    # select the record for the current date
    query = f"SELECT * FROM c WHERE c.id = '{date}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

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

def latest_dashboard_data():
    container = _get_container("control", "daily_dashboard")

    # select the record for the current date
    query = f"SELECT * FROM c ORDER BY c.id DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if items:
        return items[0]
    else:
        return None
    
def insert_blog_post(url, lastmod):
    container = _get_container("content", "blog_posts")

    item = {
        "id": url.replace("/", "|"),
        "url": url,
        "lastmod": lastmod
    }
    container.upsert_item(item)