import app_config
from fredapi import Fred
from social_media import SocialMediaPoster, SocialMediaDocument
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class FredContent:
    def __init__(self):
        self.api = Fred(api_key=app_config.FRED_API_KEY)
        self.poster = SocialMediaPoster()

    def generate_time_series_plot(
        self, series_id: str, chart_title: str, start_date=None, end_date=None
    ) -> tuple:
        data = self.api.get_series(
            series_id, observation_start=start_date, observation_end=end_date
        )

        # find the max value in the data
        max_value = max(data)

        # find the datetimeindex for the max value
        max_index = data.idxmax()

        # convert max index to month year
        max_index = max_index.strftime("%B %Y")

        # generate a plot and save it to a file, overwriting any existing file
        file_name = f"{series_id}.png"
        plt.plot(data)
        plt.title(chart_title)
        plt.savefig(file_name)
        plt.close()

        return file_name, max_index, max_value

    def post_egg_prices(self) -> SocialMediaDocument:
        file_name, max_index, max_value = self.generate_time_series_plot(
            series_id="APU0000708111", chart_title="Egg prices", start_date="2024-01-01"
        )
        caption = f"Since January 2024, the highest price of eggs was in {max_index}, at ${max_value:.2f} per dozen."
        id = self.poster.generate_and_queue_document(
            text=caption, img_file=file_name, hashtags=["AreWeGreatAgainYet"]
        )
        return self.poster.post_with_id(id)
            
    def post_gas_prices(self) -> SocialMediaDocument:
        file_name, max_index, max_value = self.generate_time_series_plot(
            series_id="GASREGW", chart_title="Gas prices", start_date="2024-01-01"
        )
        caption = f"Since January 2024, the highest nationwide average price of regular gas was in {max_index}, at ${max_value:.2f} per gallon."
        id = self.poster.generate_and_queue_document(
            text=caption, img_file=file_name, hashtags=["AreWeGreatAgainYet"]
        )
        return self.poster.post_with_id(id)
