from typing import Literal
from pydantic import BaseModel, Field
from uuid import uuid4

class SocialMediaDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    service: Literal["Bluesky", "LinkedIn"] = Field(default="Bluesky")
    after_utc: str = Field(default="2000-01-01T00:00:00Z")
    text: str = Field(default="")
    image_url: str | None = Field(default=None)
    img_file: str | None = Field(default=None)
    url: str | None = Field(default=None)
    url_title: str | None = Field(default=None)
    hashtags: list[str] | None = Field(default=None)
    emojis: list[str] | None = Field(default=None)
    posted_utc: str | None = Field(default=None)
    posted_uri: str | None = Field(default=None)
    result_message: str | None = Field(default=None)
    result_code: int | None = Field(default=None)

    def result(self) -> tuple[str | None, int | None]:
        return self.result_message, self.result_code


class SocialMediaPostResult(BaseModel):
    posted_utc: str
    posted_uri: str
    result_message: str
    result_code: int