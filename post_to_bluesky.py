from bsky_bridge import BskySession, post_text
import app_config

def post_to_bsky(message):
    print(f"Posting to BlueSky with user {app_config.BSKY_USER} and app password {app_config.BSKY_APP_PWD}")

    session = BskySession(app_config.BSKY_USER, app_config.BSKY_APP_PWD)
    print(f"Posting {message} to BlueSky...")
    response = post_text(session, message)
    print(response)