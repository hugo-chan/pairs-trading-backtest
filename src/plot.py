import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

def plot_cumpnl(data_dir):
    df = pd.read_csv(data_dir)
    assert "Cum P&L" in list(df.columns)
    dates = pd.to_datetime(df["Date"])
    
    ax = plt.gca()
    # format ticks
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())

    plt.plot(dates, df['Cum P&L'], linewidth = 1.0)
    plt.show()   


if  __name__ == "__main__":
    plot_cumpnl("../data/nasdaq_e-mini.csv")
    plt.show()
