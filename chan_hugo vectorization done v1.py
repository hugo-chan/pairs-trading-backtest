#!/usr/bin/env python
# coding: utf-8

# In[548]:


import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

# read into dataframes
ES = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ES.csv") # convert to raw string
NQ = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/NQ.csv")
CL = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/CL.csv")
NG = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/NG.csv")
ZB = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ZB.csv")
ZN = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ZN.csv")
specs = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/contract_specs.csv")


# In[549]:


ESvNQ = pd.merge(ES[['Date', 'Close']], NQ[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_ES', '_NQ'))
ESvNQ.set_index('Date', drop = True, inplace = True) # set date to be index
ESvNQ.fillna(method = 'ffill')


# In[550]:


CLvNG = pd.merge(CL[['Date', 'Close']], NG[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_CL', '_NG'))
pd.to_datetime(CLvNG['Date'])
CLvNG.set_index('Date', drop = True, inplace = True)
CLvNG.fillna(method = 'ffill')


# In[551]:


ZBvZN = pd.merge(ZB[['Date', 'Close']], ZN[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_ZB', '_ZN'))
pd.to_datetime(ZBvZN['Date'])
ZBvZN.set_index('Date', drop = True, inplace = True)
ZBvZN.fillna(method = 'ffill')


# In[552]:


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


# In[553]:


def set_previous_pos(x): # helper function to set previous position to a value
    global previous_position
    previous_position = x


# In[554]:


def determine_position_1(entry): # determines first class's position today based on yesterday's position
    global previous_position
    if previous_position == 0: # previous day was no position
        if entry['Ratio'] <= entry['Buy Enter']:
            set_previous_pos(1) # set today's position as new previous position
            return 1
        elif entry['Ratio'] < entry['Sell Enter']:
            set_previous_pos(0)
            return 0
        elif entry['Ratio'] >= entry['Sell Enter']:
            set_previous_pos(-1)
            return -1
        else: 
            print("determine_position_1: error")
    elif previous_position == 1: # previous day was long A short B
        if entry['Ratio'] < entry['Buy Exit']:
            set_previous_pos(1)
            return 1
        elif entry['Ratio'] < entry['Sell Enter']:
            set_previous_pos(0)
            return 0
        elif entry['Ratio'] >= entry['Sell Enter']:
            set_previous_pos(-1)
            return -1
        else:
            print("determine_position_1: error")
    elif previous_position == -1: # previous day was short A long B
        if entry['Ratio'] <= entry['Buy Enter']:
            set_previous_pos(1)
            return 1
        elif entry['Ratio'] <= entry['Sell Exit']:
            set_previous_pos(0)
            return 0
        elif entry['Ratio'] > entry['Sell Exit']:
            set_previous_pos(-1)
            return -1;
        else:
            print("determine_position_1: error")
    else:
        print("determine_position_1: error")
        set_prev_position(99)
        return 99


# In[555]:


def determine_position_2(entry): # determines second class' position today based on first class' position
    if entry['M1_Position'] == 0: return 0
    elif entry['M1_Position'] == 1: return -1
    elif entry['M1_Position'] == -1: return 1


# In[556]:


def set_previous_price(x): # helper function to set previous price to a specified value
    global previous_price
    previous_price = x


# In[557]:


def calculate_pd_1(entry): # calculates price delta for the first class (-1 multiplied if short position)
    global previous_price
    if previous_position == 0 or previous_price == -99: # previous day no position, so no profit/loss, can set delta = 0
        set_previous_pos(entry['M1_Position']) # set today's position as the new previous position
        set_previous_price(entry[0])
        return 0
    else: # previous day has position
        price_delta = entry.iloc[0] - previous_price
        if previous_position == -1: 
            price_delta = price_delta * -1 # if short position in the market, multiply -1 for subsequent profit calculation
        set_previous_pos(entry['M1_Position']) 
        set_previous_price(entry[0]) # set today's price as the new previous price
        return price_delta


# In[558]:


def calculate_pd_2(entry): # calculates price delta for the second class (-1 multiplied if short position)
    global previous_price
    if previous_position == 0 or previous_price == -99: # previous day no position, so no profit/loss, can set delta = 0
        set_previous_pos(entry['M2_Position']) 
        set_previous_price(entry[1])
        return 0
    else: # previous day has position
        price_delta = entry.iloc[1] - previous_price
        if previous_position == -1:
            price_delta = price_delta * -1
        set_previous_pos(entry['M2_Position'])
        set_previous_price(entry[1])
        return price_delta


# In[559]:


def find_first_date(specs): # helper function that returns the first trading day of 2007 based on the pair
    if (specs[0]["Class"] == 'ES' and specs[1]["Class"] == 'NQ') or (specs[0]["Class"] == 'CL' and specs[1]["Class"] == 'NG'):
        return "1/3/07"
    else:
        return "1/2/07"


# In[560]:


def trade_logic(df, specs, z_enter, z_exit, look_back):
    start_date = "1/1/07"
    end_date = "12/31/19"
    end_date2 = "1/2/20"
    global previous_position # denoting the previous day's position
    previous_position = 0 # initialize no position
    global previous_price # denoting the previous day's closing price
    previous_price = -99
    specs = obtain_specs(df, specs) # obtain specificiations for this pair
    first_date = find_first_date(specs) # find the first trading day of 2007 for this pair
    
    df = df[df.index.get_loc(first_date) - look_back: ] # slice df to remove anything before first_date - look_back
    df = df[pd.to_datetime(df.index) <= pd.to_datetime(end_date2)]
        # slice df; one extra day included for price delta calculation of the last day, this will be removed later
    df['Ratio'] = df.iloc[:, 0] / df.iloc[:, 1]
    df['Moving Average'] = df['Ratio'].rolling(look_back).mean().shift(1) # calculate look_back mean
    df['Moving SD'] = df['Ratio'].rolling(look_back).std().shift(1) # calculate look_back sd
    df = df[pd.to_datetime(start_date) <= pd.to_datetime(df.index)] # slice df to remove look_back days
    # use look_back mean and sd to calculate thresholds
    df['Buy Enter'] = df['Moving Average'] - (z_enter * df['Moving SD'])
    df['Buy Exit'] = df['Moving Average'] - (z_exit * df['Moving SD'])
    df['Sell Exit'] = df['Moving Average'] + (z_exit * df['Moving SD'])
    df['Sell Enter'] = df['Moving Average'] + (z_enter * df['Moving SD'])
    # determine position by comparing ratio with threshold
    df['M1_Position'] = df.apply(determine_position_1, axis = 1)
    df['M2_Position'] = df.apply(determine_position_2, axis = 1)
    # calculate price delta: use a global var to remember ytd's price, calculate one day late, and then shifting up
    set_previous_pos(0) # reset previous position to 0 because iterating from first_date
    df['M1 Price Delta'] = df.apply(calculate_pd_1, axis = 1)
    df['M1 Price Delta'] = df['M1 Price Delta'].shift(-1)
    set_previous_pos(0) # reset previous position to 0 because iterating from first_date
    df['M2 Price Delta'] = df.apply(calculate_pd_2, axis = 1)
    df['M2 Price Delta'] = df['M2 Price Delta'].shift(-1)
    # calculate transaction costs
    transcost_1 = (specs[0]['Multiplier'] * specs[0]['Tick Size']) + specs[0]['Exchange Fees'] + specs[0]['Commission'] + specs[0]['NFA Fees']
    transcost_2 = (specs[1]['Multiplier'] * specs[1]['Tick Size']) + specs[1]['Exchange Fees'] + specs[1]['Commission'] + specs[1]['NFA Fees']
    # calculate P&L using price delta and transaction costs
    df['M1_P&L'] = (df['M1 Price Delta'] * specs[0]['Multiplier']) - transcost_1
    df['M1_P&L'] = df['M1_P&L'].where(df['M1_Position'] != 0, 0)
    df['M2_P&L'] = (df['M2 Price Delta'] * specs[1]['Multiplier']) - transcost_2
    df['M2_P&L'] = df['M2_P&L'].where(df['M2_Position'] != 0, 0)
    df['P&L'] = df['M1_P&L'] + df['M2_P&L']
    # print(df.loc[:'12/31/19', ['M1_Position', 'M2_Position', 'M1_P&L', 'M2_P&L', 'P&L']])
    return (df.loc[:'12/31/19', ['M1_Position', 'M2_Position', 'M1_P&L', 'M2_P&L', 'P&L']]) # slice desired columns


# In[561]:


return_df_ESvNQ = trade_logic(ESvNQ, specs, 2, 1, 252)
return_df_ESvNQ.to_csv("stocks.csv")
return_df_CLvNG = trade_logic(CLvNG, specs, 2, 1, 252)
return_df_CLvNG.to_csv("energies.csv")
return_df_ZBvZN = trade_logic(ZBvZN, specs, 2, 1, 252)
return_df_ZBvZN.to_csv("bonds.csv")


# In[ ]:




