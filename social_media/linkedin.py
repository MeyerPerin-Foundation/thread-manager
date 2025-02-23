import requests
import json
import app_config
import logging
from datetime import datetime, timezone
from social_media.document import SocialMediaDocument, SocialMediaPostResult

logger = logging.getLogger("tm-linkedin")
logger.setLevel(logging.DEBUG)

class LinkedIn:

    def __init__(self):
        pass

    def make_hashtags(self, hashtags=None) -> str:
        hashtags_text = ""

        if hashtags is None:
            hashtags = []

        for hashtag in hashtags:
            # if the hashtag does not start with a #, add it
            if not hashtag.startswith("#"):
                hashtag = "#" + hashtag
            hashtags_text += f" {hashtag}"
            # trim the leftmost space
            hashtags_text = hashtags_text.lstrip()
            hashtags_text = "\n\n" + hashtags_text
        
        return hashtags_text

    def make_headers(self):
        return {
                "Authorization": f"Bearer {app_config.LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202501"
            }

    def make_result(self, action, code, posted_uri) -> SocialMediaPostResult:
        return SocialMediaPostResult(
            result_message=action,
            result_code=200,
            posted_uri=posted_uri,
            posted_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def make_image_uri(self, image_url = None) -> str:
        if image_url is not None:
            # initialize the upload
            data = {}
            with open("social_media_templates/li_initialize_upload.json") as json_file:
                data = json.load(json_file)
                data["initializeUploadRequest"]["owner"] = f"{app_config.LINKEDIN_PERSON_ID}"
            
            endpoint = "https://api.linkedin.com/rest/images?action=initializeUpload"
            response = requests.post(
                endpoint, headers=self.make_headers(), data=json.dumps(data)
            )
            response_json = response.json()

            if response_json["value"] is not None:
                upload_url = response_json["value"]["uploadUrl"]
                logger.info(f"Initialized upload to LinkedIn: {upload_url}")
                image_uri = response_json["value"]["image"]
                image_bytes = requests.get(image_url).content

                headers = {
                    "Authorization": f"Bearer {app_config.LINKEDIN_ACCESS_TOKEN}",
                }
                # upload
                response = requests.put(upload_url, headers=headers, data=image_bytes)
                response.raise_for_status()

                logger.info(f"Uploaded image to LinkedIn: {image_url}")
                return image_uri
            else: 
                logger.error(f"Error initializing upload to LinkedIn: {response.text}")

                return None
        else:
            logger.error(f"Error: image_url is None")
            return None
                  
    def post_document(self, document: SocialMediaDocument) -> SocialMediaDocument:
        # extract the components of the document
        text = document.text
        hashtags = document.hashtags
        target_url = document.urls[0] if document.urls else None
        url_title = document.url_titles[0] if document.url_titles else None

        result = None
        # decide what type of post to make
        if target_url is not None:
            # if there is a target url, post a link
            result = self.post_article(text, target_url, url_title, image_urls=document.image_urls, hashtags=hashtags)
        else:
            result = self.post(text, hashtags=hashtags, image_urls=document.image_urls)

        # update the document with the result      
        # get a string representing the current time in UTC
        document.posted_utc = result.posted_utc
        document.posted_uri = result.posted_uri
        document.result_message = result.result_message
        document.result_code = result.result_code

        return document

    def post(self, text, image_urls, img_alts=None, hashtags=None) -> SocialMediaPostResult:
        
        posted_uri = ""
        logger.info(f"Posting text to LinkedIn:\n{text}\n")

        hashtags = self.make_hashtags(hashtags)
        if hashtags:
            text += hashtags

        data = {}
        with open("social_media_templates/li_text.json") as json_file:
            data = json.load(json_file)
            data["author"] = f"{app_config.LINKEDIN_PERSON_ID}"
            data["commentary"] = f"{text}"

        image_uris = []

        for image_url in image_urls:
            image_uris.append(self.make_image_uri(image_url))

        medias = []
        for image_uri in image_uris:
            media = {}
            media["id"] = image_uri
            medias.append(media)

        data["content"] = {}
        if len(image_uris) == 1:
            data["content"]["media"] = medias[0]
        elif len(image_uris) > 1:
            data["content"]["multiImage"] = {}
            data["content"]["multiImage"]["images"] = medias

        # use requests to post the data to the LinkedIn API
        endpoint = "https://api.linkedin.com/rest/posts"
        response = requests.post(
            endpoint, headers=self.make_headers(), data=json.dumps(data)
        )

        # check if the response is successful
        if response.status_code == 201:            
            logger.info(f"Posted to LinkedIn: {posted_uri}")
            action = "OK"
            code = response.status_code
            # get the response header x-restli-id
            posted_uri = response.headers["x-restli-id"]
        else:
            logger.error(f"Error posting to LinkedIn: {response.text}")
            action = f"Error: {response.status_code}."
            action += "\nDetails: " + response.text
            code = response.status_code

        return self.make_result(action, code, posted_uri)

    def post_comment(self, post_uri, text) -> SocialMediaPostResult:
        logger.info(f"Posting comment to LinkedIn {post_uri}:\n{text}\n")

        try:
            data = {}
            with open("social_media_templates/li_comment.json") as json_file:
                data = json.load(json_file)
                data["actor"] = f"{app_config.LINKEDIN_PERSON_ID}"
                data["object"] = f"{post_uri}"
                data["message"] = f"{text}"

            # use requests to post the data to the LinkedIn API
            endpoint = "https://api.linkedin.com/rest/socialActions/{post_id}/comments"

            response = requests.post(
                endpoint, headers=self.make_headers(), data=json.dumps(data)
            )

            # check if the response is successful
            if response.status_code == 201:
                logger.info(f"Posted comment to LinkedIn: {post_uri}")
                action = "OK"
                code = response.status_code
            else:
                logger.error(f"Error posting comment to LinkedIn: {action}")
                action = f"Error: {response.status_code}."
                action += "\nDetails: " + response.text
                code = response.status_code

        except Exception as e:
            action = f"Error: {e}"
            logger.error(f"Error: {e}")
            code = 400


    def post_article(self, text, target_url, url_title = None, image_urls = None, image_alts=None, hashtags=None) -> SocialMediaPostResult:
        
        logger.info(f"Posting article to LinkedIn:\n{text}\n{target_url}\n")

        if image_urls is None:
            image_url = None
        else:
            image_url = image_urls[0]

        if url_title:
            title = url_title
        else:
            title = target_url

        hashtags = self.make_hashtags(hashtags)
        if hashtags:
            text += hashtags


        posted_uri = ""
        code = 400
        data = {}

        with open("social_media_templates/li_article.json") as json_file:
            data = json.load(json_file)
            data["author"] = f"{app_config.LINKEDIN_PERSON_ID}"
            data["commentary"] = f"{text}"
            data["content"]["article"]["source"] = target_url
            data["content"]["article"]["title"] = title
            data["content"]["article"]["thumbnail"] = self.make_image_uri(image_url)

        # use requests to post the data to the LinkedIn API
        endpoint = "https://api.linkedin.com/rest/posts"
        response = requests.post(
            endpoint, headers=self.make_headers(), data=json.dumps(data)
        )
        # check if the response is successful
        if response.status_code == 201:
            posted_uri = response.headers["x-restli-id"]
            logger.info(f"Posted article to LinkedIn: {posted_uri}")
            action = "OK"
            code = response.status_code
            # get the response header x-restli-id
        else:
            logger.error(f"Error posting article to LinkedIn: {response.text}")
            action = f"Error: {response.status_code}."
            action += "\nDetails: " + response.text
            code = response.status_code

        return self.make_result(action, code, posted_uri)


if __name__ == "__main__":
    l = LinkedIn()
    d = SocialMediaDocument(
        text="Large Language Models like ChatGPT sure look like magic. And, like magic, it may be super interesting to pull back the curtain and understand how the magic trick works. \n\nStephen Wolfram wrote an introductory article on What Is ChatGPT Doing … and Why Does It Work? in February 2023, just a few months after the release of ChatGPT. \n\nThe article is also available as a book. Even though there was a lot of evolution in the field of LLMs since then, the article is still a great introduction to the topic. I love that article, and frequently point beginners to it. And they hate it, because it gets very technical very quickly. Therefore, I’ll try to summarize below the main ideas of that article in a way that is more accessible.",
        hashtags=["TestingLinkedinAPI", "SundayProgramming", "WeirdWaysToHaveFun"],
        urls=["https://meyerperin.org/posts/2024-12-09-understanding-llms.html"],
        url_titles=["Understanding how LLMs work"],
        image_urls=[
            "https://meyerperin.org/images/embeddings.png"
        ],
    )
    l.post_document(d)