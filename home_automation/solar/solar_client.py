from eg4_solar_client import EG4Client
from dotenv import load_dotenv
from mpfutils.cosmosdb import CosmosDBContainer
import os
import pprint

class SolarClient:

    def __init__(self):
        self.midbox_sn = os.getenv("EG4_GRIDBOSS_SN")
        self.main_inverter_sn = os.getenv("EG4_MAIN_INVERTER_SN")
        self.solar_client = EG4Client(os.getenv("EG4_ACCOUNT"), os.getenv("EG4_PASSWORD"), self.midbox_sn, self.main_inverter_sn)
        self.db_client = CosmosDBContainer("home_automation", "daily_energy_summaries", endpoint=os.getenv("COSMOS_ENDPOINT"), key=os.getenv("COSMOS_KEY"))

    def update_year_month(self, year, month):
        # convert the year to a four digit string
        str_year = str(year)

        # convert the month to a two digit string
        str_month = str(month).zfill(2)

        d = self.solar_client.get_month_summary(year, month)
        for doc in d["data"]:
            # convert the day to a two digit string
            str_day = str(doc["day"]).zfill(2)
            # 
            id = f"{midbox_sn}-{str_year}-{str_month}-{str_day}"
            doc["id"] = id
            doc["midbox_sn"] = midbox_sn
            doc["year"] = year
            doc["month"] = month
            doc["date"] = f"{str_year}-{str_month}-{str_day}"

            for key in ["ePvDay", "eChgDay", "eDisChgDay", "eExportDay", "eImportDay", "eConsumptionDay", "eGenDay"]:
                doc[key] = float(doc[key] / 10.0)

            self.db_client.upsert_item(doc)

    def get_energy(self, start_date, end_date):
            # Query for documents whose 'date' is between the given range
        query = "SELECT * FROM c WHERE c.date >= @start AND c.date <= @end"
        parameters = [
            {'name': '@start', 'value': start_date},
            {'name': '@end',   'value': end_date}
        ]
        results = self.db_client.run_query(query=query, parameters=parameters, results_as_list=True)
        return results