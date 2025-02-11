import requests
import json
import app_config
import logging
from datetime import datetime, timezone
from social_media.document import SocialMediaDocument, SocialMediaPostResult

logger = logging.getLogger("tm-linkedin")
logger.setLevel(logging.DEBUG)


class LinkedIn:
    def post_document(self, document: SocialMediaDocument) -> SocialMediaDocument:
        # extract the components of the document
        text = document.text
        hashtags = document.hashtags
        target_url = document.url

        result = self.post(text, hashtags=hashtags, target_url=target_url)

        # get a string representing the current time in UTC
        document.posted_utc = result.posted_utc
        document.posted_uri = result.posted_uri
        document.result_message = result.result_message
        document.result_code = result.result_code

        return document

    def post(text, image=None, hashtags=None, target_url=None) -> SocialMediaPostResult:
        if target_url is not None:
            text = f"{text}\n\n{target_url}"

        if hashtags is None:
            hashtags = []

        for hashtag in hashtags:
            # if the hashtag does not start with a #, add it
            if not hashtag.startswith("#"):
                hashtag_text = "#" + hashtag
            text += f" {hashtag_text}"

        try:
            if not image:
                data = {}
                with open("social_media_templates/li_text_share.json") as json_file:
                    data = json.load(json_file)
                    data["author"] = f"{app_config.LINKEDIN_PERSON_ID}"
                    data["specificContent"]["com.linkedin.ugc.ShareContent"][
                        "shareCommentary"
                    ]["text"] = f"{text}"

                # use requests to post the data to the LinkedIn API
                endpoint = "https://api.linkedin.com/v2/ugcPosts"
                headers = {
                    "Authorization": f"Bearer {app_config.LINKEDIN_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                }
                response = requests.post(
                    endpoint, headers=headers, data=json.dumps(data)
                )

                # check if the response is successful
                if response.status_code == 201:
                    action = "OK"
                    logger.info(f"Posted to LinkedIn: {action}")
                else:
                    action = f"Error: {response.status_code}."
                    action += "\nDetails: " + response.text
                    logger.error(f"Error posting to LinkedIn: {action}")
            else:
                action = "Error: Image sharing is not supported yet."
                logger.error(action)
        except Exception as e:
            action = f"Error: {e}"
            logger.error(f"Error: {e}")
            return SocialMediaPostResult(
                result_message=action,
                result_code=400,
                posted_uri="",
                posted_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

        return SocialMediaPostResult(
            result_message=action,
            result_code=response.status_code,
            posted_uri="",
            posted_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
