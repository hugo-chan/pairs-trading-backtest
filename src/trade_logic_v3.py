# In[83]:
import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

# read into dataframes
ESvNQ = pd.read_csv(r"../data/nasdaq_e-mini.csv") # convert to raw string
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

    def _calc_ratio_thresholds(df):
        last_date = df['Ratio'].last_valid_index()
        df_sliced = df.iloc[df.index.get_loc(last_date) - (look_back - 1):, :]

        # calculate price ratio
        df_sliced["Ratio"] = df_sliced.loc[:, "Close 1"] / df_sliced.loc[:, "Close 2"]
        
        # calculate rolling mean and SD of ratio
        df_sliced["Moving Average"] = df_sliced["Ratio"].rolling(look_back).mean().shift(1)
        df_sliced["Moving SD"] = df_sliced["Ratio"].rolling(look_back).std().shift(1)

        # slice look_back dates
        df_sliced = df_sliced.iloc[look_back:, :]     

        # calculate thresholds
        df_sliced['Buy Enter'] = df_sliced['Moving Average'] - (z_enter * df_sliced['Moving SD'])
        df_sliced['Buy Exit'] = df_sliced['Moving Average'] - (z_exit * df_sliced['Moving SD'])
        df_sliced['Sell Exit'] = df_sliced['Moving Average'] + (z_exit * df_sliced['Moving SD'])
        df_sliced['Sell Enter'] = df_sliced['Moving Average'] + (z_enter * df_sliced['Moving SD'])

        print(df_sliced)

        

        return df

    def _determine_positions(df):
        for i in range(len(df.index)):
            # get previous position
            if not i:
                prev_pos = 0
                prev_price = 0
            else:
                prev_pos = df.loc[df.index[i - 1], 'M1 Position']
            
            date = df.index[i]
            ratio = df.loc[date, 'Ratio']
            pos = 0
            
            if prev_pos == 0:
                if  ratio <= df.loc[date, 'Buy Enter']:
                    pos = 1
                elif ratio >= df.loc[date, 'Sell Enter']:
                    pos = -1
            elif prev_pos == 1:
                if ratio < df.loc[date, 'Buy Exit']:
                    pos = 1
                elif ratio >= df.loc[date, 'Sell Enter']:
                    pos = -1
            else:
                if ratio <= df.loc[date, 'Buy Enter']:
                    pos = 1
                elif ratio > df.loc[date, 'Sell Exit']:
                    pos = -1

            df.loc[date, 'M1 Position'] = pos




        df['M2 Position'] = -1 * df['M1 Position'] 
        return df
    
    df = _calc_ratio_thresholds(df)
    df = _determine_positions(df)


    return df

    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df[["M1 Position", "M2 Position"]])
    

# In[97]:

return_df_ESvNQ = trade_logic(ESvNQ, specs, 2, 1, 252)
# return_df_ESvNQ.to_csv(r"../data/nasdaq_e-mini.csv")