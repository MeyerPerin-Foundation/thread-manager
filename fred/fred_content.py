from . import app_config
from fredapi import Fred
import matplotlib.pyplot as plt
from PIL import Image


class FredContent:
    def __init__(self):
        self.api = Fred(api_key=app_config.FRED_API_KEY)

    def generate_time_series_plot(self, series_id: str, start_date=None, end_date=None) -> tuple:
        data = self.api.get_series(series_id, observation_start=start_date, observation_end=end_date)
        
        # find the max value in the data
        max_value = max(data)

        # find the datetimeindex for the max value
        max_index = data.idxmax()
       
        # convert max index to month year
        max_index = max_index.strftime("%B %Y")


        caption = f"Since January 2024, the highest price of eggs was in {max_index}, at ${max_value:.2f} per dozen."

        # generate a plot and save it to a file, overwriting any existing file
        file_name = f"{series_id}.png"
        plt.plot(data)
        plt.savefig(file_name)
        plt.close()

        return caption, file_name
        
    def egg_prices(self):
        return self.generate_time_series_plot(series_id="APU0000708111", start_date="2024-01-01")


if __name__ == "__main__":
    fred = FredContent()
    caption, file_name = fred.egg_prices()

    print(caption)

    # show image
    img = Image.open(file_name)
    img.show()
    
