import requests
import app_config

def get_follower_count() -> int:
    url = f"https://graph.threads.net/v1.0/{app_config.THREADS_USER_ID}/threads_insights?metric=followers_count&access_token={app_config.THREADS_TEST_TOKEN}"
    response_json = requests.get(url).json()
    
    try:
        followers_count = response_json["data"][0]["total_value"]["value"]
        return followers_count
    except (KeyError, IndexError):
        return None