from pydantic import BaseModel

class SocialMediaDocument(BaseModel):
    text: str
    image_url: str | None = None
    img_file: str | None = None
    url: str | None = None
    url_title: str | None = None
    hashtags: list[str] | None = None
    emojis: list[str] | None = None

class SocialMediaPostResult(BaseModel):
    service: str
    success: bool
    result_message: str
    result_code: int
    posted_uri: str | None = None
    posted_utc_time: str | None = None

    def result(self) -> tuple[str, int]:
        return self.result_message, self.result_code

