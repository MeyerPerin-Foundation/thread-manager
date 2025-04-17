import logging
from utils.cosmosdb import _get_container
from datetime import datetime, timezone, UTC, timedelta
from zoneinfo import ZoneInfo
from typing import List

from social_media import SocialMediaPoster
from content.birds import BirdContent
from content.countdown import CountdownContent
from content.fred import FredContent
from content.blog_promo import BlogPromoContent
from content.imgflip import ImgflipContent
from content.financial.alpha_vantage import AlphaVantageContent
from content.folder.folder_content import FolderContent

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
        service = schedule["service"]

        id = None
        if command == "bird":
            logger.info("Scheduling bird content")
            b = BirdContent()
            id = b.generate_birdbuddy_post(after_utc=after_utc)

        elif command == "countdown":
            logger.info("Scheduling countdown content")
            c = CountdownContent()
            #TODO: Add service to days until
            id = c._generate_days_until_document(
                event_name = schedule["command_parameters"]["event"],
                event_date = schedule["command_parameters"]["target_date"],
                plural = schedule["command_parameters"]["plural"],
                stop = schedule["command_parameters"]["stop"],
                after_utc = after_utc,                
            )

        elif command == "folder":
            logger.info("Scheduling folder content")
            f = FolderContent()
            # check if there's a folder name in the command parameters
            folder_name = schedule["command_parameters"].get("folder_name")
            if folder_name is None:
                id = f.queue_post(service=service, after_utc=after_utc)
            else:
                id = f.queue_post(service=service, folder_name=folder_name, after_utc=after_utc)

        elif command == "fred":
            logger.info("Posting Fred content")
            f = FredContent()
            id = f.queue_time_series_plot(
                service = service,
                series_id = schedule["command_parameters"]["series_id"],
                series_description = schedule["command_parameters"]["series_description"],
                series_highlight = schedule["command_parameters"].get("series_highlight", "max"),
                start_date = schedule["command_parameters"]["start_date"],
                end_date = schedule["command_parameters"].get("end_date"),
                hashtags = schedule["command_parameters"].get("hashtags"),
                after_utc = None
            )
            poster = SocialMediaPoster()
            poster.post_with_id(id)


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

            e = s.check_new_max_ePvDay()
            if e is not None:
                logger.info(f"New max ePvDay: {e}")
                # create a post with the new max ePvDay
                poster = SocialMediaPoster()
                
                text = f"Today, my solar panel installation generated {e} kWh of energy, a record for the last 365 days. It uses Enphase panels, EG4 GridBoss + 2 FlexBoss + batteries. Installed by Texas Solar Professional. Links below."
                urls = ["https://eg4electronics.com/", "https://www.texassolar.pro/", "https://www.enphase.com/en-us/"]
                url_titles = ["EG4", "Texas Solar Professional", "Enphase"]
                image_urls = ["https://threadmanager.blob.core.windows.net/post-images/enphase.jpg"]
                after_utc = "2020-01-01T00:00:00Z"

                id = poster.generate_and_queue_document(
                    text = text,
                    service = "Bluesky",
                    after_utc = after_utc,
                    image_urls = image_urls,
                    urls = urls,
                    url_titles = url_titles,
                )
                poster.post_with_id(id)
                logger.info(f"Posted new max ePvDay: {e}")


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
                service = service,
                message = "",
                template = schedule["command_parameters"]["template"],
                text0 = schedule["command_parameters"]["text0"],
                text1 = schedule["command_parameters"]["text1"],
                max_font_size = schedule["command_parameters"].get("max_font_size"),
                after_utc = after_utc,
            )
        elif command == "post":
            logger.info("Adding post to schedule")
            poster = SocialMediaPoster()
            id = poster.generate_and_queue_document(
                text = schedule["command_parameters"]["post_text"],
                service = service,
                after_utc = after_utc,
                image_urls = [schedule["command_parameters"].get("image_url")],
            )
        elif command == "alpha_vantage":
            logger.info("Posting Alpha Vantage content")
            a = AlphaVantageContent()
            id = a.queue_symbol_plot(
                service = service,
                symbol = schedule["command_parameters"]["av_symbol"],
                symbol_name = schedule["command_parameters"]["av_symbol_name"],
                series_description = schedule["command_parameters"]["av_series_description"],
                period_name = schedule["command_parameters"].get("av_period_name"),
                start_date = schedule["command_parameters"].get("av_start_date"),
                end_date = schedule["command_parameters"].get("av_end_date"),
                condition_type = schedule["command_parameters"].get("av_condition_type"),
                condition_value = schedule["command_parameters"].get("av_condition_value"),
                after_utc = None,
            )
            poster = SocialMediaPoster()
            poster.post_with_id(id)

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

    def delete_old_tasks(self):
        now = datetime.now(UTC).isoformat()
        query = f"SELECT * FROM c WHERE c.delete_after_utc < '{now}'"
        items = list(self.container.query_items(query, enable_cross_partition_query=True))        
        for item in items:
            id = item["id"]
            logger.info(f"Deleting task {id} because of delete_after_utc")
            self.delete_task(id)

    def get_task(self, id: str) -> dict:
        return self.container.read_item(item=id, partition_key=id)

    def update_task(self, id, schedule: dict):
        self.container.replace_item(item=id, body=schedule)

    def delete_task(self, id: str):
        logger.info(f"Deleting task {id}")
        self.container.delete_item(id, partition_key=id)

    def create_task(self, schedule: dict):
        self.container.create_item(schedule)

if __name__ == "__main__":
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

    e = s.check_new_max_ePvDay()
    if e is not None:
        logger.info(f"New max ePvDay: {e}")
        # create a post with the new max ePvDay
        poster = SocialMediaPoster()
        
        text = f"Today, my solar panel installation generated {e} kWh of energy, a record for the last 365 days. It uses Enphase panels, EG4 GridBoss + 2 FlexBoss + batteries. Installed by Texas Solar Professional. Links below."
        urls = ["https://eg4electronics.com/", "https://www.texassolar.pro/", "https://www.enphase.com/en-us/"]
        url_titles = ["EG4", "Texas Solar Professional", "Enphase"]
        image_urls = ["https://threadmanager.blob.core.windows.net/post-images/enphase.jpg"]
        after_utc = "2020-01-01T00:00:00Z"

        id = poster.generate_and_queue_document(
            text = text,
            service = "Bluesky",
            after_utc = after_utc,
            image_urls = image_urls,
            urls = urls,
            url_titles = url_titles,
        )
        poster.post_with_id(id)
        logger.info(f"Posted new max ePvDay: {e}")
