import app_config
import cosmosdb

def checkUserIsAuthorized(user) -> bool:
    return cosmosdb.check_user_in_db(user)

def checkApiAuthorized(token) -> bool:
    # Parse out the bearer
    token = token.split(" ")[1]

    if token != app_config.API_TOKEN:
        return False
    else:
        return True
