from bsky_bridge import BskySession, post_text
import app_config

def post_to_bsky(message):
    session = BskySession(app_config.BSKY_USER, app_config.BSKY_APP_PWD)
    response = post_text(session, message)
    print(response)