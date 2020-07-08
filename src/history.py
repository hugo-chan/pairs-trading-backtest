import requests
import quandl
import pandas as pd
from datetime import date
import os
import configparser


class History:

    match = {
        "NASDAQ": {
            "code": "NASDAQOMX/COMP",
            "price_label": "Index Value"
        },
        "E-MINI": {
            "code": "CHRIS/CME_ES1",
            "price_label": "Last"
        },
        "CRUDEOIL": {
            "code":"EIA/PET_RWTC_D"
        }
    }

    def __init__(self, name):
        self.name = name
        self.code = self.match.get(self.name).get("code") # get subscription code
        self.update()


    def get_history(self, start_date):
        today = date.today()

        price_label = self.match.get(self.name).get("price_label")
        df = quandl.get(self.code, start_date=start_date, end_date=str(today))[[price_label]] # get data

        # rename to same index name and variable name
        df.index.names = ['Date']
        df.rename(columns = {df.columns[0]: "Price?"}, inplace = True)

        return df

    def update(self):

        class ColumnNameError(Exception):
            pass

        folder_dir = "./data"
        if not os.path.exists(folder_dir):
            os.mkdir(folder_dir)

        data_dir = f"{folder_dir}/{self.name.lower()}.csv"

        try:
            self.df = pd.read_csv(data_dir)
            print(self.df)
            if list(self.df.columns) != ['Date', 'Price?']:
                raise ColumnNameError
            else:
                last_date = self.df['Date'].iloc[self.df['Price?'].last_valid_index()] # last date with price defined
                print(last_date)
                # get last date with price defined
                # update from last date to today


        except (FileNotFoundError, pd.errors.EmptyDataError, ColumnNameError):
            self.df = self.get_history("2003-1-21")
            self.df.to_csv(data_dir)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("../config.ini")
    quandl.ApiConfig.api_key = config.get("keys", "key")

    History("NASDAQ")
    # History("E-MINI")
