from atproto import Client
import app_config

def get_follower_count() -> int:
    client = Client()
    client.login(app_config.BSKY_USER, app_config.BSKY_APP_PWD)
    profile = client.get_profile(app_config.BSKY_USER)
    return profile["followers_count"]

