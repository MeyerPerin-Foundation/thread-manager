import app_config
import json
import requests
from atproto import Client, client_utils
from time import sleep


def post_to_instagram(text, image = None, hashtags = None):
    print(f"Right now, I don't know how to post to Instagram")
    return "OK", 200

def post_to_threads(text, image = None, hashtags = None):
    print(f"Posting {text} to Threads")
    message = text

    # remove high unicode characters
    message = message.encode('ascii', 'ignore').decode('ascii')
    
    # if the message is in quotes, remove the quotes
    if message.startswith('"') and message.endswith('"'):
        message = message[1:-1]

    if message.startswith("'") and message.endswith("'"):
        message = message[1:-1]

    if hashtags is not None:
        message = f"{message} #{hashtags[0]}"

    payload = {
        "access_token": app_config.THREADS_TEST_TOKEN,
        "text": message,
        "media_type": "TEXT"
    }

    if image is not None:
        payload["image_url"] = image
        payload["media_type"] = "IMAGE"

    post_url = f"https://graph.threads.net/v1.0/{app_config.THREADS_USER_ID}/threads/"

    response = requests.post(post_url, json=payload)

    if response.status_code == 200:
        # get response id
        response_json = response.json()
        creation_id = response_json["id"]
        print("Waiting 10 seconds for Threads to process the post")
        sleep(10)
    else:
        return "Error", 400
    
    publish_payload = {
        "access_token": app_config.THREADS_TEST_TOKEN,
        "creation_id": creation_id
    }

    publish_url = f"https://graph.threads.net/v1.0/{app_config.THREADS_USER_ID}/threads_publish/"

    response = requests.post(publish_url, json=publish_payload)

    if response.status_code == 200:
        return "OK", 200
    else:
        return "Error", 400

def post_to_bluesky(text, image = None, hashtags = None, emojis = None):
    message = text

    # remove high unicode characters
    message = message.encode('ascii', 'ignore').decode('ascii')
    
    # if the message is in quotes, remove the quotes
    if message.startswith('"') and message.endswith('"'):
        message = message[1:-1]

    if message.startswith("'") and message.endswith("'"):
        message = message[1:-1]
    
    if emojis is not None:
        for emoji in emojis:
            message += emoji

    text_builder = client_utils.TextBuilder()
    text_builder.text(message + "\n")

    for hashtag in hashtags:
        # if the hashtag does not start with a #, add it
        if not hashtag.startswith("#"):
            hashtag_text = "#" + hashtag
        text_builder.tag(hashtag_text, hashtag)

    client = Client()
    client.login(app_config.BSKY_USER, app_config.BSKY_APP_PWD)

    if image is None:
        post = client.send_post(text_builder)
    else:
        # get image data from url
        image_data = requests.get(image).content
        post = client.send_image(text_builder, image=image_data, image_alt="")

    post_uri = post.uri

    print(f"Result of post_to_bluesky: {post_uri}")
    return "OK", 200

def post_to_linkedin(text, image = None, hashtags = None):
        # return not implemented
        return "Not Implemented", 501

        data = {}
        with open('text_share.json') as json_file:
            data = json.load(json_file)
            data['author'] = f"{app_config.LINKEDIN_PERSON_ID}"
            data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] = f"{text}"

        # use requests to post the data to the LinkedIn API
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {app_config.LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # check if the response is successful
        if response.status_code == 201:
            action = f"Success."
            return action, 201
        else:
            action = f"Error: {response.status_code}."
            action += "\nDetails: " + response.text
            return action, 400

def post(standard_document):
    if standard_document is None:
        return None

    # The standard document is a JSON with text and optional image, and booleans for threads, instagram, linkedin and bluesky
    if 'text' in standard_document:
        text = standard_document['text']
    else:
        return None
    
    # Check if the message of the day has an image
    if 'image' in standard_document:
        image = standard_document['image']
    else:
        image = None

    if 'hashtags' in standard_document:
        hashtags = standard_document['hashtags']
    else:
        hashtags = None

    if 'topic' in standard_document:
        topic = standard_document['topic']
    else:
        topic = None

    if 'emojis' in standard_document:
        emojis = standard_document['emojis']

    # Check if the message of the day has a threads boolean
    if 'threads' in standard_document and standard_document['threads']:
        post_to_threads(text, image, hashtags)
    
    # Check if the message of the day has a instagram boolean
    if 'instagram' in standard_document and standard_document['instagram']:
        post_to_instagram(text, image, hashtags)

    # Check if the message of the day has a linkedin boolean
    if 'linkedin' in standard_document and standard_document['linkedin']:
        post_to_linkedin(text, image, hashtags)

    # Check if the message of the day has a bluesky boolean
    if 'bluesky' in standard_document and standard_document['bluesky']:
        post_to_bluesky(text, image, hashtags, emojis)

    return "OK", 200
