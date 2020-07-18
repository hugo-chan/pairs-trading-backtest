# In[83]:
import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

# read into dataframes
ESvNQ = pd.read_csv(r"../data/nasdaq_e-mini3.csv") # convert to raw string
ESvNQ.set_index('Date', drop = True, inplace = True) # set date to be index
specs = pd.read_csv(r"../data/raw/contract specifications.csv")

# In[87]:


def obtain_specs(df, specs):
    # find out which pair, then index to that row using the ticker
    # store multiplier, tick size, exchange fees, commissions, NFA fees, and ticker in a dictionary
    colname = df.columns[0] # find out which pair we are looking at
    if (colname == 'Close_ES'):
        ticker_A = 'ES'
        ticker_B = 'NQ'
    elif (colname == 'Close_CL'):
        ticker_A = 'CL'
        ticker_B = 'NG'
    else:
        ticker_A = 'ZB'
        ticker_B = 'ZN'
    row_A = specs.loc[specs['Ticker'] == ticker_A] # extract the rows of interest from specs
    row_B = specs.loc[specs['Ticker'] == ticker_B]
    specs_A = {"Multiplier" : row_A.iat[0, 1], # put specifications in dictionary
              "Tick Size" : row_A.iat[0, 2],
              "Exchange Fees" : row_A.iat[0, 3],
              "Commission" : row_A.iat[0, 4],
              "NFA Fees" : row_A.iat[0, 5],
              "Class" : ticker_A}
    specs_B = {"Multiplier" : row_B.iat[0, 1],
              "Tick Size" : row_B.iat[0, 2],
              "Exchange Fees" : row_B.iat[0, 3],
              "Commission" : row_B.iat[0, 4],
              "NFA Fees" : row_B.iat[0, 5],
              "Class" : ticker_B}
    return (specs_A, specs_B) # return tuple


# In[96]:


def trade_logic(df, specs, z_enter, z_exit, look_back):

    specs = obtain_specs(df, specs) # obtain specificiations for this pair

    def _calc_ratio_thresholds(df, start):

        # get view of dataframe containing non-updated data and 252 rows before it
        df_sliced = df.iloc[start:, :]

        # calculate price ratio
        ratio = df_sliced.loc[:, "Close 1"] / df_sliced.loc[:, "Close 2"]
        # calculate rolling mean and SD of ratio
        mov_avg = ratio.rolling(look_back).mean().shift(1)
        mov_sd = df_sliced["Ratio"].rolling(look_back).std().shift(1)

        # slice look_back dates
        df_sliced = df_sliced.iloc[look_back:, :]     

        # calculate thresholds
        df_sliced['Buy Enter'] = mov_avg - (z_enter * mov_sd)
        df_sliced['Buy Exit'] = mov_avg - (z_exit * mov_sd)
        df_sliced['Sell Exit'] = mov_avg + (z_exit * mov_sd)
        df_sliced['Sell Enter'] = mov_avg + (z_enter * mov_sd)

        if start:
            return df
        else:
            return df_sliced

    def _determine_positions(df, start):

        # initialize previous position for first iteration of loop
        if start == 0:
            prev_pos = 0

            # there is no previous price, therefore backwards fill ==> P&L of first day = 0
            prev_price_1 = df.iloc[start+1]["Close 1"]
            prev_price_2 = df.iloc[start+1]["Close 2"]
        else:
            prev_pos = df.iloc[start]["M1 Position"]
            prev_price_1 = df.iloc[start]["Close 1"]
            prev_price_2 = df.iloc[start]["Close 2"]

        # get view of dataframe containing non-updated data and one row before it
        df_sliced = df.iloc[start+1:, :]

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

            df_sliced.loc[date, 'M1 Position'] = pos
            df_sliced.loc[date, 'M2 Position'] = -1 * pos


            curr_price_1 = df_sliced.loc[date, 'Close 1']
            curr_price_2 = df_sliced.loc[date, 'Close 2']

            price_delta_1 = curr_price_1 - prev_price_1
            price_delta_2 = curr_price_2 - prev_price_2

            pnl_1 = pos * price_delta_1
            pnl_2 = -1 * pos * price_delta_2
            
            if prev_pos != pos:
                # add transaction cost
                pnl_1 += 0 # todo
                pnl_2 += 0 # todo

            df_sliced.loc[date, 'M1 P&L'] = pnl_1
            df_sliced.loc[date, 'M2 P&L'] = pnl_2

            prev_pos = pos
            prev_price_1 = curr_price_1
            prev_price_2 = curr_price_2

            # compute P&L

        # print("SDFD", df_sliced)
        # print("START", start)
        if start:
            return df
        else:
            return df_sliced
    
    try:
        last_date = df['Ratio'].last_valid_index()
        last_date2 = df['M1 Position'].last_valid_index()
        assert last_date == last_date2
        ratio_start = df.index.get_loc(last_date) - (look_back - 1)
        pos_start = df.index.get_loc(last_date2)

    except KeyError:
        ratio_start = 0
        pos_start = 0

    # print(df)
    df = _calc_ratio_thresholds(df, ratio_start)
    print("SDFSDF", df)
    df = _determine_positions(df, pos_start)

    return df
    

# In[97]:

return_df_ESvNQ = trade_logic(ESvNQ, specs, 2, 1, 252)
return_df_ESvNQ.to_csv(r"../data/nasdaq_e-mini3.csv")