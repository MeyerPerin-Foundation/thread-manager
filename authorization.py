import app_config
from cosmosdb import Auth
import logging

logger = logging.getLogger("tm-auth")

def checkUserIsAuthorized(user: dict) -> bool:
    if user is None:
        return False
    
    auth = Auth()
    user_in_db  = auth.check_user_in_db(user)
    username = user.get("preferred_username")
    usersub = user.get("sub")

    if user_in_db:
        logger.info(f"Authorized user {username} with sub {usersub} ")
        return True
    else:
        logger.warning(f"NOT AUTHORIZED user {username} with sub {usersub}")
        return False


def checkApiAuthorized(token) -> bool:

    if token is None:
        return False
    
    # Parse out the bearer
    token = token.split(" ")[1]

    if token != app_config.API_TOKEN:
        return False
    else:
        return True
