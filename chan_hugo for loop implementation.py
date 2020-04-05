#!/usr/bin/env python
# coding: utf-8

# In[480]:


import pandas as pd

# read into dataframes
ES = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ES.csv") # convert to raw string
NQ = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/NQ.csv")
CL = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/CL.csv")
NG = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/NG.csv")
ZB = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ZB.csv")
ZN = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/ZN.csv")
specs = pd.read_csv(r"C:\Users\Hugo Chan\Desktop\Quant Trading Intern Project 2020/contract_specs.csv")

print(specs)


# In[481]:


ESvNQ = pd.merge(ES[['Date', 'Close']], NQ[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_ES', '_NQ'))
ESvNQ.set_index('Date', drop = True, inplace = True)
ESvNQ.fillna(method = 'ffill')


# In[482]:


CLvNG = pd.merge(CL[['Date', 'Close']], NG[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_CL', '_NG'))
pd.to_datetime(CLvNG['Date'])
CLvNG.set_index('Date', drop = True, inplace = True)
CLvNG.fillna(method = 'ffill')


# In[483]:


ZBvZN = pd.merge(ZB[['Date', 'Close']], ZN[['Date', 'Close']], on = 'Date', how = 'outer', suffixes = ('_ZB', '_ZN'))
pd.to_datetime(ZBvZN['Date'])
ZBvZN.set_index('Date', drop = True, inplace = True)
ZBvZN.fillna(method = 'ffill')


# In[484]:


def threshold(look_back_ratio, z_enter, z_exit): # computes the four thresholds for each day
    t = {"buy enter" : look_back_ratio["mean"] - (z_enter * look_back_ratio["sd"]),
        "buy exit" : look_back_ratio["mean"] - (z_exit * look_back_ratio["sd"]),
        "sell exit" : look_back_ratio["mean"] + (z_exit * look_back_ratio["sd"]),
        "sell enter" : look_back_ratio["mean"] + (z_enter * look_back_ratio["sd"])}
    return t;


# In[485]:


def look_back_ratio_info(df, i, row, look_back): # computes the mean and sd of the ratio over the last <look_back> days
        #print("this is the date we are currently on")
        #print(row)
        index = df.index.get_loc(i) # integer location of the Datetime index
        look_back_df = df.iloc[index-look_back:index] # dataframe containing the lookback region
        look_back_df = look_back_df.copy() # create a proper dataframe rather than a slice
        look_back_df['Ratio'] = look_back_df.iloc[:,0] / look_back_df.iloc[:,1]  # create ratio column in lookback df
        ratio_mean = look_back_df['Ratio'].mean() # mean for the ratio over the lookback days
        ratio_sd = look_back_df['Ratio'].std()
        look_back_ratio = {"mean" : ratio_mean, "sd" : ratio_sd}
        return look_back_ratio


# In[486]:


def determine_position(return_df, today_ratio, thresholds, i, count):
    index = return_df.index.get_loc(i) # integer location of the Datetime index in the return dataframe
    if count == 0 or (return_df.iat[index-1, 0] == 0 and return_df.iat[index-1, 1] == 0): # first day or previous day no position
        #print("no position, previous day was ", index - 1)
        if today_ratio <= thresholds["buy enter"]:
            #print("open buy position")
            return_df.iat[index, 0] = 1
            return_df.iat[index, 1] = -1
        elif today_ratio < thresholds["sell enter"]: #bruhhhh
            #print("maintain no position")
            return_df.iat[index, 0] = 0
            return_df.iat[index, 1] = 0
        elif thresholds["sell enter"] <= today_ratio:
            #print("reverse position")
            return_df.iat[index, 0] = -1
            return_df.iat[index, 1] = 1
        else:
            print("OOPPSSS")
    elif return_df.iat[index-1, 0] == 1 and return_df.iat[index-1, 1] == -1: # previous day was long A short B
        #print("long A short B, previous day was ", index - 1)
        if today_ratio < thresholds["buy exit"]:
            #print("no action")
            return_df.iat[index, 0] = 1
            return_df.iat[index, 1] = -1
        elif today_ratio < thresholds["sell enter"]:
            #print("close position")
            return_df.iat[index, 0] = 0
            return_df.iat[index, 1] = 0
        elif thresholds["sell enter"] <= today_ratio:
            #print("reverse position")
            return_df.iat[index, 0] = -1
            return_df.iat[index, 1] = 1
    elif return_df.iat[index-1, 0] == -1 and return_df.iat[index-1, 1] == 1: # previous day was short A long B
        #print("short A long B, previous day was ", index - 1)
        if today_ratio <= thresholds["buy enter"]:
            #print("reverse position")
            return_df.iat[index, 0] = 1
            return_df.iat[index, 1] = -1
        elif today_ratio <= thresholds["sell exit"]:
            #print("close position")
            return_df.iat[index, 0] = 0
            return_df.iat[index, 1] = 0
        elif thresholds["sell exit"] < today_ratio:
            #print("no action")
            return_df.iat[index, 0] = -1
            return_df.iat[index, 1] = 1
        else:
            print("OOPPSSS")
    else:
        print("SOMETHING IS WRONG")


# In[487]:


def calculate_pl(return_df, scoped_df, specs, i): # calculate profit and loss for each day
    #if i != "12/31/19": # not the last day, can calculate profit and loss
    index = scoped_df.index.get_loc(i) # integer location of the index in scoped_df, used to obtain the prices
    if return_df.iat[index, 0] == 0 and return_df.iat[index, 1] == 0: # no position, so no profit or loss
        return_df.iat[index, 2] = 0
        return_df.iat[index, 3] = 0
    else: # has position, has profit and loss
        price_A_delta = scoped_df.iat[index + 1, 0] - scoped_df.iat[index, 0]
        #print("date ", i, " price_A_delta ", price_A_delta)
        price_B_delta = scoped_df.iat[index + 1, 1] - scoped_df.iat[index, 1]
        # long A short B
        pure_profit_A = price_A_delta * specs[0]['Multiplier'] # before transaction costs
        pure_profit_B = -1 * price_B_delta * specs[1]['Multiplier'] # -1 because shorting B
        if return_df.iat[index, 0] == -1 and return_df.iat[index, 1] == 1: # short A long B
            pure_profit_A *= -1
            pure_profit_B *= -1
        transcost_A = (specs[0]['Multiplier'] * specs[0]['Tick Size']) + specs[0]['Exchange Fees'] + specs[0]['Commission'] + specs[0]['NFA Fees']
                        # ASSUMING TRANSACTION COST IS INCLUDED EVERY DAY
                        # (tick size * multiplier) + exchange fees + commissions + NFA fees
        transcost_B = (specs[1]['Multiplier'] * specs[1]['Tick Size']) + specs[1]['Exchange Fees'] + specs[1]['Commission'] + specs[1]['NFA Fees']
                        # ASSUMING TRANSACTION COST IS INCLUDED EVERY DAY
                        # (tick size * multiplier) + exchange fees + commissions + NFA fees

        actual_profit_A = pure_profit_A - transcost_A
        actual_profit_B = pure_profit_B - transcost_B

        return_df.iat[index, 2] = actual_profit_A # M1_P&L column
        return_df.iat[index, 3] = actual_profit_B # M2_P&L column


    return_df.iat[index, 4] = return_df.iat[index, 2] + return_df.iat[index, 3] # P&L column

        


# In[488]:


def obtain_specs(df, specs):
    # first need to find out which pair, then index to that row
    # then store multiplier, tick size, exchange fees, commissions, and NFA fees in a dictionary
    # return tuple containing each market's dictionary

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
    
    specs_A = {"Multiplier" : row_A.iat[0, 1], # put specs in dictionary
              "Tick Size" : row_A.iat[0, 2],
              "Exchange Fees" : row_A.iat[0, 3],
              "Commission" : row_A.iat[0, 4],
              "NFA Fees" : row_A.iat[0, 5]}
    specs_B = {"Multiplier" : row_B.iat[0, 1],
              "Tick Size" : row_B.iat[0, 2],
              "Exchange Fees" : row_B.iat[0, 3],
              "Commission" : row_B.iat[0, 4],
              "NFA Fees" : row_B.iat[0, 5]}
    
    return (specs_A, specs_B)


# In[489]:


start_date = "1/1/07"
end_date = "12/31/19"
def trade_logic(df, specs, z_enter, z_exit, look_back):
    contract_specs = obtain_specs(df, specs) # obtain contract specs for this pair
    
    # create return dataframe
    return_df = pd.DataFrame(index=df.index)
    return_df['M1_Position'] = ""
    return_df['M2_Position'] = ""
    return_df['M1_P&L'] = ""
    return_df['M2_P&L'] = ""
    return_df['P&L'] = ""
    
    count = 0 # indicator variable for whether determine_position() is being run for the first time
    for i, row in df[(pd.to_datetime(start_date) <= pd.to_datetime(df.index)) & 
                   (pd.to_datetime(df.index) <= pd.to_datetime(end_date))].iterrows(): # implement using loops for now   
        look_back_ratio = look_back_ratio_info(df, i, row, look_back) # obtain the mean and sd of ratio in past look-back days
        #print(look_back_ratio)
        thresholds = threshold(look_back_ratio, z_enter, z_exit) # obtain threshold dict
        #print(thresholds)
        today_ratio = row[0] / row[1] # today's ratio, now compare it to the thresholds
        determine_position(return_df, today_ratio, thresholds, i, count) # compute position for each day
        count = 1 
        calculate_pl(return_df, df, contract_specs, i)
        #return_df.at[i, 'M1_Position']
        #print(return_df)
    return return_df[(pd.to_datetime(start_date) <= pd.to_datetime(df.index)) & 
                   (pd.to_datetime(df.index) <= pd.to_datetime(end_date))]


# In[490]:


return_df_ESvNQ = trade_logic(ESvNQ, specs, 2, 1, 252)
return_df_ESvNQ.to_csv("ESvNQ_temp.csv")
return_df_CLvNG = trade_logic(CLvNG, specs, 2, 1, 252)
return_df_CLvNG.to_csv("CLvNG_temp.csv")
return_df_ZBvZN = trade_logic(ZBvZN, specs, 2, 1, 252)
return_df_ZBvZN.to_csv("ZBvZN_temp.csv")


# In[ ]:





# In[ ]:




