import logging
import requests
from time import sleep
from app_config import THREADS_USER_ID, THREADS_TEST_TOKEN

logger = logging.getLogger("tm-threads")
logger.setLevel(logging.DEBUG)

def post_to_threads(text, image=None, hashtags=None, url=None, url_title=None):
    logger.info(f"Posting {text} to Threads")

    message = text

    if hashtags is not None:
        message = f"{message} #{hashtags[0]}"

    if url is not None:
        if image is None:
            message = f"{message}\n\n{url}"
        else:
            logger.info("Threads does not support posts that combine images and URLs, removing URL from message")
            message = f"{message}"

    payload = {
        "access_token": THREADS_TEST_TOKEN,
        "text": message,
        "media_type": "TEXT",
    }

    if image is not None:
        payload["image_url"] = image
        payload["media_type"] = "IMAGE"

    post_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads/"

    response = requests.post(post_url, json=payload)
    logger.info(f"Threads response: {response.text}")

    if response.status_code == 200:
        # get response id
        response_json = response.json()
        creation_id = response_json["id"]
        wait = 3
        logger.info(f"Waiting {wait} seconds for Threads to process the post")
        sleep(wait)
    else:
        return "Error", 400

    publish_payload = {
        "access_token": THREADS_TEST_TOKEN,
        "creation_id": creation_id,
    }

    publish_url = (
        f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish/"
    )

    response = requests.post(publish_url, json=publish_payload)
    response_json = response.json()
    media_id = response_json["id"]
    logger.info(f"Published to Threads with media_id: {media_id}")

    if image is not None and url is not None:
        logger.info("User has provided both an image and a URL")
        logger.info(f"Posting URL {url} as a reply to {media_id}")

        # Post the URL as a reply
        reply_payload = {
            "access_token": THREADS_TEST_TOKEN,
            "text": f"{url_title}\n{url}",
            "reply_to_id": media_id,
            "media_type": "TEXT",
        }

        comment_response = requests.post(post_url, json=reply_payload)
        logging.info(f"Threads response to reply: {comment_response.text}")  

        if response.status_code == 200:
            # get response id
            comment_response_json = comment_response.json()
            comment_creation_id = comment_response_json["id"]
            wait = 3
            logger.info(f"Waiting {wait} seconds for Threads to process the post")
            sleep(wait)
        else:
            return "Error", 400

        publish_payload = {
            "access_token": THREADS_TEST_TOKEN,
            "creation_id": comment_creation_id,
        }
    
        response = requests.post(publish_url, json=publish_payload)
        response_json = response.json()
        media_id = response_json["id"]
        logger.info(f"Published comment to Threads with media_id: {media_id}")        

    if response.status_code == 200:
        return "OK", 200
    else:
        return "Error", 400
