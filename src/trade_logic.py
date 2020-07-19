import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

class TradeLogic:

    specs = {
        "nasdaq": {
            "Multiplier": 20,
            "Tick Size": 0.25,
            "Fees": 2.05
        },
        "e-mini": {
            "Multiplier": 50,
            "Tick Size": 0.25,
            "Fees": 2.05
        }
    }

    def __init__(self, name1, name2, z_enter, z_exit, window_len):
        # read into dataframes
        self.name1 = name1
        self.name2 = name2
        self.df = pd.read_csv(f"../data/{self.name1}_{self.name2}.csv")
        self.df.set_index('Date', drop = True, inplace = True)
        self.df = self.trade_logic(z_enter, z_exit, window_len)
        self.df.to_csv(f"../data/{self.name1}_{self.name2}.csv")


    def trade_logic(self, z_enter, z_exit, window_len):

        def _calc_ratio_thresholds(start):

            # get view of dataframe containing non-updated data and 252 rows before it
            df_sliced = self.df.iloc[start:, :]

            # calculate price ratio
            df_sliced["Ratio"] = df_sliced.loc[:, "Close 1"] / df_sliced.loc[:, "Close 2"]
            # calculate rolling mean and SD of ratio
            mov_avg = df_sliced["Ratio"].rolling(window_len).mean().shift(1)
            mov_sd = df_sliced["Ratio"].rolling(window_len).std().shift(1)

            # slice window_len dates
            df_sliced = df_sliced.iloc[window_len:, :]     

            # calculate thresholds
            df_sliced['Buy Enter'] = mov_avg - (z_enter * mov_sd)
            df_sliced['Buy Exit'] = mov_avg - (z_exit * mov_sd)
            df_sliced['Sell Exit'] = mov_avg + (z_exit * mov_sd)
            df_sliced['Sell Enter'] = mov_avg + (z_enter * mov_sd)

            if not start:
                self.df = df_sliced

        def _determine_positions(start):

            # initialize previous position for first iteration of loop
            if start == 0:
                prev_pos = 0
                # there is no previous price ==> P&L of first day = 0
                prev_price_1 = self.df.iloc[start+1]["Close 1"]
                prev_price_2 = self.df.iloc[start+1]["Close 2"]
                prev_cumpnl = 0
            else:
                prev_pos = self.df.iloc[start]["Position 1"]
                prev_price_1 = self.df.iloc[start]["Close 1"]
                prev_price_2 = self.df.iloc[start]["Close 2"]
                prev_cumpnl = self.df.iloc[start]["Cum P&L"]

            # get view of dataframe containing non-updated data and one row before it
            df_sliced = self.df.iloc[start+1:, :]

            for i in range(len(df_sliced.index)):
                
                date = df_sliced.index[i]
                ratio = df_sliced.loc[date, 'Ratio']
                pos = 0
                
                # compute position based on previous day's
                if prev_pos == 0:
                    if  ratio <= df_sliced.loc[date, 'Buy Enter']:
                        pos = 1
                    elif ratio >= df_sliced.loc[date, 'Sell Enter']:
                        pos = -1
                elif prev_pos == 1:
                    if ratio < df_sliced.loc[date, 'Buy Exit']:
                        pos = 1
                    elif ratio >= df_sliced.loc[date, 'Sell Enter']:
                        pos = -1
                else:
                    if ratio <= df_sliced.loc[date, 'Buy Enter']:
                        pos = 1
                    elif ratio > df_sliced.loc[date, 'Sell Exit']:
                        pos = -1

                df_sliced.loc[date, 'Position 1'] = pos
                df_sliced.loc[date, 'Position 2'] = -1 * pos

                # compute P&L
                curr_price_1 = df_sliced.loc[date, 'Close 1']
                curr_price_2 = df_sliced.loc[date, 'Close 2']

                price_delta_1 = curr_price_1 - prev_price_1
                price_delta_2 = curr_price_2 - prev_price_2

                specs1 = self.specs[self.name1]
                specs2 = self.specs[self.name2]

                # use prev_pos bc we always enter position EOD
                pnl_1 = prev_pos * price_delta_1 * specs1["Multiplier"]
                pnl_2 = -1 * prev_pos * price_delta_2 * specs2["Multiplier"]
                
                if prev_pos != pos:
                    # add transaction cost
                    pnl_1 -= (specs1["Multiplier"] * specs1["Tick Size"]) + specs1["Fees"]
                    pnl_2 -= (specs2["Multiplier"] * specs2["Tick Size"]) + specs2["Fees"]

                df_sliced.loc[date, 'P&L 1'] = pnl_1
                df_sliced.loc[date, 'P&L 2'] = pnl_2
                df_sliced.loc[date, 'P&L'] = pnl_1 + pnl_2
                df_sliced.loc[date, 'Cum P&L'] = prev_cumpnl + pnl_1 + pnl_2

                # set previous to current
                prev_pos = pos
                prev_price_1 = curr_price_1
                prev_price_2 = curr_price_2
                prev_cumpnl += pnl_1 + pnl_2

            if not start:
                self.df = df_sliced
        
        try:
            last_date = self.df['Ratio'].last_valid_index()
            last_date2 = self.df['Position 1'].last_valid_index()
            assert last_date == last_date2
            ratio_start = self.df.index.get_loc(last_date) - (window_len - 1)
            pos_start = self.df.index.get_loc(last_date2)

        except KeyError:
            # data not initialized
            ratio_start = 0
            pos_start = 0

        _calc_ratio_thresholds(ratio_start)
        _determine_positions(pos_start)

        return self.df