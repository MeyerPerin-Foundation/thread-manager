from azure.cosmos import CosmosClient, exceptions, PartitionKey
import app_config

def checkUserIsAuthorized(app_config, user) -> bool:
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client(app_config.COSMOS_DATABASE)
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


def checkApiAuthorized(token) -> bool:
    if token != app_config.API_TOKEN:
        return False
    else:
        return True
