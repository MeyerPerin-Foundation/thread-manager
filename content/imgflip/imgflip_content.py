from social_media import SocialMediaPoster
import requests
import datetime
import app_config

class ImgflipContent:

    def __init__(self):
        self.poster = SocialMediaPoster()
        self.username = app_config.IMGFLIP_USERNAME
        self.password = app_config.IMGFLIP_PASSWORD
        self.known_templates = {
            "Distracted Boyfriend": 112126428,
            "Drake Hotline Bling": 101511,
            "Two Buttons": 100947736,
            "Change My Mind": 101869573,
            "Expanding Brain": 100947736,
            "Is This a Pigeon?": 1102023,
            "Surprised Pikachu": 123999232,
            "Worst day of my life": 118505186,
            "What a week huh": 333869421,
        }


    def get_template_id(self, template_name: str) -> int | None:
        if template_name in self.known_templates:
            return self.known_templates[template_name]
        else:
            return int(template_name)

    def queue_meme(
        self,
        message: str,
        template: str,
        text0: str,
        text1: str,
        max_font_size = None,
        service = "Bluesky",
        after_utc: str = "2000-01-01T00:00:00Z",
    ) -> str | None:

        url = self.generate_meme(template, text0, text1, max_font_size, after_utc)
        if url is None:
            return None

        tags = ["UngovMemes"]

        d = self.poster.generate_and_queue_document(
            text=message,
            after_utc=after_utc,
            service=service,
            image_urls=[url],
            hashtags=tags,
        )

        return d
        
    def generate_meme(
        self,
        template: str,
        text0: str,
        text1: str,
        max_font_size: int | None = None,
        after_utc: str | None = None,
    ) -> str | None:

        text0 = self.text_replace(text0, after_utc)
        text1 = self.text_replace(text1, after_utc)
        template_id = self.get_template_id(template)

        if max_font_size is not None:
            max_font_size = int(max_font_size)

        url = "https://api.imgflip.com/caption_image"
        payload = {
            "template_id": template_id,
            "username": self.username,
            "password": self.password,
            "text0": text0,
            "text1": text1,
            "max_font_size": max_font_size,
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            j = response.json()
            if j["success"]:
                return j["data"]["url"]
            else:
                return None
        else:
            return None

    def text_replace(self, text: str, after_utc = None) -> str:
        if after_utc is None or after_utc == "2000-01-01T00:00:00Z" or after_utc <= "2000-01-02T00:00:00Z":
            anchor_date = datetime.date.today()
        else:
            anchor_date = datetime.datetime.fromisoformat(after_utc).date()

        # look for @yesterday
        if "@yesterday_month" in text:
            yesterday = anchor_date - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime("%B")
            text = text.replace("@yesterday_month", yesterday_str)
        if "@today_month" in text:
            today = anchor_date
            today_str = today.strftime("%B")
            text = text.replace("@today_month", today_str)
        if "@tomorrow_month" in text:
            tomorrow = anchor_date + datetime.timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%B")
            text = text.replace("@tomorrow_month", tomorrow_str)
        if "@yesterday_bdy" in text:
            yesterday = anchor_date - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime("%B, %d %Y")
            text = text.replace("@yesterday_bdy", yesterday_str)
        if "@today_bdy" in text:
            today = anchor_date
            today_str = today.strftime("%B, %d %Y")
            text = text.replace("@today_bdy", today_str)
        if "@tomorrow_bdy" in text:
            tomorrow = anchor_date + datetime.timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%B, %d %Y")
            text = text.replace("@tomorrow_bdy", tomorrow_str)
        if "@yesterday_weekday" in text:
            yesterday = anchor_date - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime("%A")
            text = text.replace("@yesterday_weekday", yesterday_str)
        if "@today_weekday" in text:
            today = anchor_date
            today_str = today.strftime("%A")
            text = text.replace("@today_weekday", today_str)
        if "@tomorrow_weekday" in text:
            tomorrow = anchor_date + datetime.timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%A")
            text = text.replace("@tomorrow_weekday", tomorrow_str)            
        if "@yesterday" in text:
            yesterday = anchor_date - datetime.timedelta(days=1)
            yesterday_str = yesterday.strftime("%B %d")
            text = text.replace("@yesterday", yesterday_str)
        if "@today" in text:
            today = anchor_date
            today_str = today.strftime("%B %d")
            text = text.replace("@today", today_str)
        if "@tomorrow" in text:
            tomorrow = anchor_date + datetime.timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%B %d")
            text = text.replace("@tomorrow", tomorrow_str)

        
        return text

if __name__ == "__main__":
    imgflip = ImgflipContent()
    url = imgflip.queue_meme(
        message="Testing my automated meme generator part deux...",
        template="333869421",
        text0="What a year, huh?",
        text1="Captain, it's @today_month",
        max_font_size=50,
    )
    print(url)