import app_config
import json
import requests
from atproto import Client, client_utils


def post_to_instagram(text, image = None, hashtags = None):
    print(f"Right now, I don't know how to post to Instagram")
    return "OK", 200

def post_to_threads(text, image = None, topic = None):
    print(f"Right now, I don't know how to post to Threads")
    return "OK", 200

def post_to_bluesky(text, image = None, hashtags = None):
    message = text

    # remove high unicode characters
    message = message.encode('ascii', 'ignore').decode('ascii')
    
    # if the message is in quotes, remove the quotes
    if message.startswith('"') and message.endswith('"'):
        message = message[1:-1]

    if message.startswith("'") and message.endswith("'"):
        message = message[1:-1]
    
    text_builder = client_utils.TextBuilder()
    text_builder.text(message)
    for hashtag in hashtags:
        # if the hashtag does not start with a #, add it
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag
        text_builder.tag(hashtag, hashtag)

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

    # Check if the message of the day has a threads boolean
    if 'threads' in standard_document and standard_document['threads']:
        post_to_threads(text, image, topic)
    
    # Check if the message of the day has a instagram boolean
    if 'instagram' in standard_document and standard_document['instagram']:
        post_to_instagram(text, image, hashtags)

    # Check if the message of the day has a linkedin boolean
    if 'linkedin' in standard_document and standard_document['linkedin']:
        post_to_linkedin(text, image, hashtags)

    # Check if the message of the day has a bluesky boolean
    if 'bluesky' in standard_document and standard_document['bluesky']:
        post_to_bluesky(text, image, hashtags)

    return "OK", 200
