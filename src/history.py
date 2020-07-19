import requests
import quandl
import pandas as pd
import datetime
import os
import configparser

from trade_logic import TradeLogic


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

    def __init__(self, name1, name2):        
        self.name1 = name1
        self.name2 = name2
        # get subscription codes
        self.code1 = self.match.get(self.name1).get("code")
        self.code2 = self.match.get(self.name2).get("code") 
        self.update()
        self.calc_pnl()


    def get_history(self, start_date, name, code):
        today = datetime.date.today()

        price_label = self.match.get(name).get("price_label")
        # get data
        df = quandl.get(code, start_date=start_date, end_date=str(today))[[price_label]]

        # rename to same index name and variable name
        df.index.names = ['Date']
        df.rename(columns = {df.columns[0]: "Close"}, inplace = True)
        # remove nan rows
        df.dropna(subset=["Close"], inplace=True)

        return df

    def update(self):

        class ColumnNameError(Exception):
            pass

        folder_dir = "../data"
        if not os.path.exists(folder_dir):
            os.mkdir(folder_dir)

        data_dir = f"{folder_dir}/{self.name1.lower()}_{self.name2.lower()}.csv"

        try:
            self.df = pd.read_csv(data_dir)

            if not all(col in list(self.df.columns) for col in ['Date', 'Close 1', 'Close 2']):
                # csv file has not been initialized
                raise ColumnNameError
            else:
                # get last date with price defined
                last_date = self.df['Date'].iloc[self.df['Close 1'].last_valid_index()]
                update_date = str(datetime.datetime.strptime(last_date, "%Y-%m-%d") + datetime.timedelta(days=1))

                header = False

        except (FileNotFoundError, pd.errors.EmptyDataError, ColumnNameError):
            update_date = "2003-1-21"
            header = True

        finally:
            new_df1 = self.get_history(update_date, self.name1, self.code1)
            new_df2 = self.get_history(update_date, self.name2, self.code2)

            new_df = pd.merge(
                new_df1[['Close']], new_df2[['Close']], 
                left_index = True, right_index = True, 
                how = 'outer', suffixes = (' 1', ' 2'), sort = True
            )
            new_df.fillna(method = 'ffill', inplace = True)

            new_df.to_csv(data_dir, mode = "a", header = header)

    def calc_pnl(self):
        TradeLogic(self.name1.lower(), self.name2.lower())


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("../config.ini")
    key = config.get("keys", "key")
    quandl.ApiConfig.api_key = key

    History("NASDAQ", "E-MINI")