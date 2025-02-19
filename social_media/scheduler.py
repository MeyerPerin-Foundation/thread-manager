import logging
from utils.cosmosdb import _get_container
from datetime import datetime, timezone, UTC, timedelta
from zoneinfo import ZoneInfo
from typing import List

from social_media import SocialMediaPoster
from content.birds import BirdContent
from content.countdown import CountdownContent
from content.too_far import TooFarContent
from content.ungovernable import UngovernableContent
from content.fred import FredContent
from content.blog_promo import BlogPromoContent
from content.imgflip import ImgflipContent

from home_automation.solar import SolarClient

from dashboard import DashboardDB


logger = logging.getLogger("tm-scheduler")
logger.setLevel(logging.DEBUG)


class SocialMediaScheduler:

    def __init__(self):
        self.container = _get_container("posts", "schedules")

    def list_expired_schedules (self) -> List[dict]:

        now = datetime.now(UTC).isoformat()
        query = f"SELECT * FROM c WHERE c.last_scheduled_time_utc < '{now}'"
        return list(self.container.query_items(query, enable_cross_partition_query=True))

    def update_schedule(self, schedule: dict):
        last = schedule["last_scheduled_time_utc"] 
        next = schedule["next_scheduled_time_utc"]
        schedule["last_scheduled_time_utc"] = next
        unit = schedule["repeat_unit"]
        every = schedule["repeat_every"]
        
        new_time = datetime.fromisoformat(next) + timedelta(**{unit: every})
        schedule["next_scheduled_time_utc"] = new_time.isoformat()
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
            logger.info("Scheduling Fred content")
            f = FredContent()
            id = f.queue_time_series_plot(
                series_id = schedule["command_parameters"]["series_id"],
                series_description = schedule["command_parameters"]["series_description"],
                series_highlight = schedule["command_parameters"].get("series_highlight", "max"),
                start_date = schedule["command_parameters"]["start_date"],
                end_date = schedule["command_parameters"].get("end_date"),
                hashtags = schedule["command_parameters"].get("hashtags"),
                after_utc = after_utc,
            )

        elif command == "blog":
            logger.info("Scheduling blog promo content")
            b = BlogPromoContent()
            id = b.generate_blog_promo(after_utc=after_utc)

        elif command == "refresh_solar":
            logger.info("Executing solar refresh")            
            s = SolarClient()

            # get current year and month
            now = datetime.now()
            year = now.year
            month = now.month

            # get last year month
            last_month = month - 1
            if last_month == 0:
                last_month = 12
                last_year -= 1
            else:
                last_year = year

            s.update_year_month(year, month)
            s.update_year_month(last_year, last_month)

        elif command == "collect_bird_postcards":
            logger.info("Collecting bird postcards")
            birds = BirdContent()
            now = datetime.now(UTC).isoformat()
            last_update = birds.get_latest_bird_update()

            birds.upload_birds(since=last_update)
            birds.set_latest_bird_update(now)

        elif command == "refresh_dashboard":
            logger.warning("Refresh dashboard not implemented")
        
        elif command == "imgflip":
            logger.info("Scheduling Imgflip content")
            i = ImgflipContent()
            id = i.queue_meme(
                message = "",
                template = schedule["command_parameters"]["template"],
                text0 = schedule["command_parameters"]["text0"],
                text1 = schedule["command_parameters"]["text1"],
                max_font_size = schedule["command_parameters"].get("max_font_size"),
                after_utc = after_utc,
            )

        else:
            logger.warning(f"Unknown command: {command}")
                
        return id

    def next_utc_time(self, hours: str, minutes: str, tz_str: str) -> str:
        hour = int(hours)
        minute = int(minutes)
        
        local_tz = ZoneInfo(tz_str)
        
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(local_tz)
        
        # Build a candidate datetime for today in the target timezone with the given hour and minute.
        candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the candidate time is not in the future relative to now_local, move to the next day.
        if candidate <= now_local:
            candidate += timedelta(days=1)
        
        # Convert the candidate time back to UTC.
        candidate_utc = candidate.astimezone(timezone.utc)
        
        # Return the UTC time as an ISO 8601 formatted string.
        return candidate_utc.strftime("%Y-%m-%dT%H:%M:%S%UTC")

    def list_tasks(self) -> List[dict]:
        query = "SELECT * FROM c ORDER BY c.next_scheduled_time_utc"
        return list(self.container.query_items(query, enable_cross_partition_query=True))

    def get_task(self, id: str) -> dict:
        return self.container.read_item(item=id, partition_key=id)

    def update_task(self, id, schedule: dict):
        self.container.replace_item(item=id, body=schedule)

    def delete_task(self, id: str):
        self.container.delete_item(id, partition_key=id)

    def create_task(self, schedule: dict):
        self.container.create_item(schedule)
