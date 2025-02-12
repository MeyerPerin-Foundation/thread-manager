# auth_utils.py
import utils.auth.authorization as authorization
from flask import current_app, request

def check_auth() -> bool:
    # Make sure that auth has been initialized!
    return authorization.checkUserIsAuthorized(
        current_app.auth.get_user()
    ) or authorization.checkApiAuthorized(request.headers.get("Authorization"))