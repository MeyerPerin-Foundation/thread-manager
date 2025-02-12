import logging
from utils.cosmosdb import _get_container
from datetime import datetime, timezone
from typing import List

from social_media import SocialMediaPoster
from content.birds import BirdContent
from content.countdown import CountdownContent
from content.too_far import TooFarContent
from content.ungovernable import UngovernableContent
from content.fred import FredContent
from content.blog_promo import BlogPromoContent

logger = logging.getLogger("tm-scheduler")
logger.setLevel(logging.DEBUG)


class SocialMediaScheduler:

    def __init__(self):
        self.container = _get_container("posts", "schedules")

    def list_expired_schedules (self) -> List[dict]:

        now = datetime.datetime.now(datetime.UTC).isoformat()
        query = f"SELECT * FROM c WHERE c.last_scheduled_time_utc < '{now}'"
        return list(self.container.query_items(query, enable_cross_partition_query=True))

    def update_schedule(self, schedule: dict):
        last = schedule["last_scheduled_time_utc"] 
        next = schedule["next_scheduled_time_utc"]
        schedule["last_scheduled_time_utc"] = next
        unit = schedule["repeat_unit"]
        every = schedule["repeat_every"]
        
        new_time = next + timedelta(**{unit: every})
        schedule["next_scheduled_time_utc"] = new_time        
        self.container.upsert_item(schedule)

    def generate_post_document(self, schedule: dict):
        command = schedule["command"]
        after_utc = schedule["next_scheduled_time_utc"]

        id = None
        if command == "bird":
            logger.info("Scheduling bird content")
            b = BirdContent()
            id = b.generate_birdbuddy_post(after_utc=after_utc)
        elif command == "countdown":
            logger.info("Scheduling countdown content")
            c = CountdownContent()
            id = c._generate_days_until_document(
                event_name = schedule["command_parameters"]["event"],
                event_date = schedule["command_parameters"]["target_date"],
                plural = schedule["command_parameters"]["plural"],
                stop = schedule["command_parameters"]["stop"],
                after_utc = after_utc,                
            )
        elif command == "too_far":
            logger.info("Scheduling Too Far content")
            t = TooFarContent()
            id = t.generate_too_far(after_utc=after_utc)
        elif command == "ungovernable":
            logger.info("Scheduling ungovernable content")
            u = UngovernableContent()
            id = u.queue_ungovernable(after_utc=after_utc)
        elif command == "fred":
            logger.warning("Fred is not implemented yet")
            pass

        return id