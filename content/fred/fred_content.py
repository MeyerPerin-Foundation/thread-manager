import app_config
from fredapi import Fred
from social_media import SocialMediaPoster, SocialMediaDocument
from utils.azstorage import AzureStorageClient
import uuid
import pandas as pd
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tenacity import retry, wait_exponential, stop_after_attempt

class FredContent:
    def __init__(self):
        self.api = Fred(api_key=app_config.FRED_API_KEY)
        self.poster = SocialMediaPoster()

    @retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(3))
    def get_series(self, 
        series_id: str,
        observation_start, 
        observation_end) -> pd.Series:
        data = self.api.get_series(series_id, observation_start, observation_end)
        return data
    

    def queue_time_series_plot(
        self, 
        series_id: str, 
        series_description: str, 
        series_highlight: str = "max", 
        start_date=None, 
        end_date=None, 
        hashtags=None,
        after_utc=None
    ) -> str | None:

        tags = ["FredChartGenerator"]

        if hashtags is not None:
            tags.extend(hashtags)

        if start_date is None:
            raise ValueError("start_date is required")

        series_frequency = self.api.get_series_info(series_id).frequency_short

        data = self.get_series(
            series_id, observation_start=start_date, observation_end=end_date
        )
        
        if after_utc is None:
            after_utc = "2000-01-01T00:00:00Z"

        if series_highlight == "max":
            # find the max value in the data
            value = max(data)
            index = data.idxmax()
        else:
            raise ValueError("Invalid series_highlight value.")

        # adjust index to match the series frequency
        if series_frequency == "M":
            index = index.strftime("%B %Y")
        elif series_frequency == "Q":
            index = index.strftime("%B %Y")
        elif series_frequency == "A":
            index = index.strftime("%Y")
        else:
            index = index.strftime("%B %d, %Y")

        # convert start_date to datetime
        start_date = pd.to_datetime(start_date)
        since = start_date.strftime("%B %d, %Y")

        # generate the caption
        if series_highlight == "max":
            caption = f"The highest {series_description} since {since} was in {index}, at ${value:.2f}."
    
        # capitalize the series_description
        chart_title = series_description.capitalize()

        # create a plot and upload it to Azure Storage
        buf = io.BytesIO()
        plt.plot(data)
        plt.title(chart_title)
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        blob_name = f"fred-{str(uuid.uuid4())}.png"
        azs = AzureStorageClient()
        image_url = azs.upload_blob("post-images", blob_name, buf.getvalue())

        id = self.poster.generate_and_queue_document(
            text=caption, image_url=image_url, hashtags=tags, after_utc=after_utc
        )

        return id


        
