import app_config
import json
import requests
from atproto import Client, client_utils
from time import sleep


def post_to_instagram(text, image = None, hashtags = None):
    print(f"Right now, I don't know how to post to Instagram")
    return "OK", 200

def post_to_threads(text, image = None, hashtags = None, url = None):
    print(f"Posting {text} to Threads")

    message = text

    if hashtags is not None:
        message = f"{message} #{hashtags[0]}"

    if url is not None:
        message = f"{message}\n\n{url}"

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
        wait = 3
        print(f"Waiting {wait} seconds for Threads to process the post")
        sleep(wait)
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

def post_to_bluesky(text, image = None, hashtags = None, emojis = None, url = None):
    message = text
    
    if emojis is not None:
        for emoji in emojis:
            message += emoji

    text_builder = client_utils.TextBuilder()
    text_builder.text(message + "\n")

    if hashtags is None:
        hashtags = []

    for hashtag in hashtags:
        # if the hashtag does not start with a #, add it
        if not hashtag.startswith("#"):
            hashtag_text = "#" + hashtag
        text_builder.tag(hashtag_text, hashtag)

    if url is not None:
        text_builder.link("\nRead more...", url)    

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

def post_to_linkedin(text, image = None, hashtags = None, url = None):

    if url is not None:
        text = f"{text}\n\n{url}"
    

    if hashtags is None:
        hashtags = []

    for hashtag in hashtags:
        # if the hashtag does not start with a #, add it
        if not hashtag.startswith("#"):
            hashtag_text = "#" + hashtag
        text += f" {hashtag_text}"
    
    try:
        if image is None:
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
    except Exception as e:
        print(f"Error: {e}") 
        return f"Error: {e}", 400
    
    return "OK", 200
    

def post(standard_document):
    if standard_document is None:
        return "No content", 204

    # The standard document is a JSON with text and optional image, and booleans for threads, instagram, linkedin and bluesky
    if 'text' in standard_document:
        text = standard_document['text']
    else:
        return None
    
    # Check if the document has an image
    if 'image' in standard_document:
        image = standard_document['image']
    else:
        image = None

    if 'hashtags' in standard_document:
        hashtags = standard_document['hashtags']
    else:
        hashtags = None

    if 'emojis' in standard_document:
        emojis = standard_document['emojis']
    else:
        emojis = None

    if 'url' in standard_document:
        url = standard_document['url']
    else:
        url = None

    # Check if the document has a bluesky boolean
    if 'bluesky' in standard_document and standard_document['bluesky']:
        post_to_bluesky(text, image=image, hashtags=hashtags, emojis=emojis, url=url)

    # Check if the document has a threads boolean
    if 'threads' in standard_document and standard_document['threads']:
        post_to_threads(text, image=image, hashtags=hashtags, url=url)
    
    # Check if the document has a linkedin boolean
    if 'linkedin' in standard_document and standard_document['linkedin']:
        post_to_linkedin(text, image=image, hashtags=hashtags, url=url)

    # Check if the document has a instagram boolean
    if 'instagram' in standard_document and standard_document['instagram']:
        post_to_instagram(text, image, hashtags)

    return "OK", 200
