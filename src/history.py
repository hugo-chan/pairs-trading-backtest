import requests
import quandl
import pandas as pd
import datetime
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
        today = datetime.date.today()

        price_label = self.match.get(self.name).get("price_label")
        df = quandl.get(self.code, start_date=start_date, end_date=str(today))[[price_label]] # get data

        # rename to same index name and variable name
        df.index.names = ['Date']
        df.rename(columns = {df.columns[0]: "Price?"}, inplace = True)
        # remove nan rows
        df.dropna(subset=["Price?"], inplace=True)

        return df

    def update(self):

        class ColumnNameError(Exception):
            pass

        folder_dir = "../data"
        if not os.path.exists(folder_dir):
            os.mkdir(folder_dir)

        data_dir = f"{folder_dir}/{self.name.lower()}.csv"

        try:
            self.df = pd.read_csv(data_dir)

            print("orig", self.df)
            # print(self.df)
            if list(self.df.columns) != ['Date', 'Price?']:
                # csv file has not been initialized
                raise ColumnNameError
            else:
                # get last date with price defined
                last_date = self.df['Date'].iloc[self.df['Price?'].last_valid_index()]
                next_date = str(datetime.datetime.strptime(last_date, "%Y-%m-%d") + datetime.timedelta(days=1))
                print("next_date", next_date)

                # df for next date to today
                new_df = self.get_history(next_date)

                # append df to existing csv
                new_df.to_csv(data_dir, mode = "a", header = False)

        except (FileNotFoundError, pd.errors.EmptyDataError, ColumnNameError):
            self.df = self.get_history("2003-1-21")
            self.df.to_csv(data_dir)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("../config.ini")
    key = config.get("keys", "key")
    quandl.ApiConfig.api_key = key

    History("NASDAQ")
    History("E-MINI")
