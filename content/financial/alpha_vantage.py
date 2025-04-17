import requests
import app_config
from mpfutils.azstorage import AzsContainerClient
import pandas as pd
import matplotlib.pyplot as plt
from uuid import uuid4
from social_media import SocialMediaPoster
import yfinance as yf
import io

import logging
logger = logging.getLogger("tm-scheduler")
logger.setLevel(logging.DEBUG)

class AlphaVantageContent:

    def __init__(self, api_key=None):
        if api_key:
            self.api_key = api_key
        else:
            # get the API key from the config file
            self.api_key = app_config.ALPHA_VANTAGE_API_KEY

    def get_daily_close(self, symbol, start_date = None, end_date = None):
        if start_date and end_date:
            data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True)
        elif start_date:
            data = yf.download(symbol, start=start_date, auto_adjust=True)
        else:
            data = yf.download(symbol, auto_adjust=True)

        data = data[["Close"]].reset_index()
        data.rename(columns={"Close": "Value", "Date": "Date"}, inplace=True)

        print(data.head())

        # return filtered_data

    def generate_post_text(self, data, series_description, period_name = None, condition_type=None, condition_value=None):
        # get the start date of the series
        start_date = list(data.keys())[0]
        # get the end date of the series
        end_date = list(data.keys())[-1]

        # calculate the return between end_date and start_date
        start_value = float(data[start_date])
        end_value = float(data[end_date])
        returns = (end_value - start_value) / start_value * 100

        time_frame = f"From {start_date} to {end_date}"
        if period_name:
            time_frame = period_name

        epilogue = "Data as of market close on " + end_date + "."

        if condition_type and condition_value:
            if condition_type == "greater":
                if returns > condition_value:
                    logger.info(f"Condition met: {returns} > {condition_value}")
                    text = f"{time_frame}, {series_description} returns were {returns:.2f}%.\n{epilogue}"
                else: 
                    logger.info(f"Condition not met: {returns} > {condition_value}")
                    text = ""
            if condition_type == "less":
                if returns < condition_value:
                    logger.info(f"Condition met: {returns} < {condition_value}")
                    text = f"{time_frame}, {series_description} returns were {returns:.2f}%.\n{epilogue}"
                else:
                    logger.info(f"Condition not met: {returns} < {condition_value}")
                    text = ""
        else:
            text = f"{time_frame}, {series_description} returns were {returns:.2f}%.\n{epilogue}"
        
        return text


    def generate_chart(self, data, title):
        # Convert data to DataFrame
        df = data
        print(df.head())
        df.sort_values('Date', inplace=True)

        # Plot
        plt.figure(figsize=(12, 9))
        plt.plot(df['Date'], df['Value'], marker='o', linestyle='-')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title(title)
        plt.xticks(rotation=80)
        plt.grid(True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # upload to Azure
        azs = AzsContainerClient(container_name="post-images")
        # generate a unique name for the blob
        blob_name = f"av-{uuid4()}.png"
        
        url = azs.upload_blob(blob_name, buf, overwrite=True)
        buf.close()
        plt.close()
        return url

        
    def queue_symbol_plot(
        self,
        symbol: str, 
        symbol_name: str,
        series_description: str | None = None,
        period_name: str | None = None,
        condition_type: str | None = None,
        condition_value: float | None = None,
        service: str = "Bluesky",
        start_date=None, 
        end_date=None, 
        hashtags=None,
        after_utc=None
    ) -> str | None:        
        data = self.get_daily_close(symbol, start_date, end_date)
        text = self.generate_post_text(data, series_description, period_name, condition_type, condition_value)
        if text == "":
            return None
        image_url = self.generate_chart(data, symbol_name + " Daily Close Prices")

        if after_utc is None:
            after_utc = "2000-01-01T00:00:00Z"

        poster = SocialMediaPoster()
        id = poster.generate_and_queue_document(
            service=service,
            text=text, 
            image_urls=[image_url], 
            hashtags=hashtags, 
            after_utc=after_utc
        )

        return id

if __name__ == "__main__":
    a = AlphaVantageContent(app_config.ALPHA_VANTAGE_API_KEY)
    a.get_daily_close("^GSPC", start_date = "2025-03-01")
    # a.generate_chart(a.get_daily_close("^GSPC"), "S&P 500 ETF Daily Close Prices")


    # a.queue_symbol_plot(
    #     "SPXX", 
    #     "S&P 500 ETF", 
    #     "S&P 500 ETF (SPX)", 
    #     "Since Trump's inauguration", 
    #     start_date="2025-01-20", 
    #     condition_type="less",
    #     condition_value=-7,
    #     after_utc="2025-01-20T00:00:00Z")


