from bsky_bridge import BskySession, post_text
import app_config
import json
import requests

def post_to_instagram(text, image = None):
    print(f"Right now, I don't know how to post to Instagram")
    return "OK", 200

def post_to_threads(text, image = None):
    print(f"Right now, I don't know how to post to Threads")
    return "OK", 200

def post_to_bluesky(text, image = None):
    message = text
    session = BskySession(app_config.BSKY_USER, app_config.BSKY_APP_PWD)
    response = post_text(session, message)

    print(f"Result of post_to_bluesky:\n{response}")
    return "OK", 200

def post_to_linkedin(text, image = None):
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

    # The standard document is a JSON with post_text and optional post_image, and booleans for threads, instagram, linkedin and bluesky
    if 'text' in standard_document:
        text = standard_document['text']
    else:
        return None
    
    # Check if the message of the day has a post_image
    if 'image' in standard_document:
        image = standard_document['image']
    else:
        image = None

    # Check if the message of the day has a threads boolean
    if 'threads' in standard_document and standard_document['threads']:
        post_to_threads(text, image)
    
    # Check if the message of the day has a instagram boolean
    if 'instagram' in standard_document and standard_document['instagram']:
        post_to_instagram(text, image)

    # Check if the message of the day has a linkedin boolean
    if 'linkedin' in standard_document and standard_document['linkedin']:
        post_to_linkedin(text, image)

    # Check if the message of the day has a bluesky boolean
    if 'bluesky' in standard_document and standard_document['bluesky']:
        post_to_bluesky(text, image)

    return "OK", 200
