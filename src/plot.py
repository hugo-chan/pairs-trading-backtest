import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import datetime

def plot_cumpnl(data_dir):
    df = pd.read_csv(data_dir)
    assert "Cum P&L" in list(df.columns)
    dates = pd.to_datetime(df["Date"])
    
    plt.figure(num=None, figsize=(10.5, 6), dpi=100)
    
    ax = plt.gca()
    # format ticks
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())

    plt.plot(dates, df['Cum P&L'], linewidth = 1.0)
    plt.title("Performance of Strategy")
    plt.ylabel("P&L (USD)")
    plt.xlabel("Time")
    plt.figtext(0.13, 0.02, f"Last updated: {datetime.date.today()}", ha='left', fontsize=9)
    plt.savefig("../data/pnl.png")

if  __name__ == "__main__":
    plot_cumpnl("../data/nasdaq_e-mini.csv")