# Pairs-Trading-Backtest

A program to backtest a pairs trading strategy on pairs of financial instruments. The most up-to-date data is obtained from Quandl API, to which the strategy is applied. The daily position on the pair and the corresponding profit and loss are determined for each day in a CSV file. The cumulative profit and loss graph is generated.

The code in this repo currently backtests NASDAQ and E-mini S&P 500 futures, but more pairs can be easily added as long as you have the Quandl code for the financial instrument.

## About the Strategy
The core of this strategy is mean reversion. For each day, the strategy compares the price ratio with a rolling simple moving average. If the price ratio is significantly greater or smaller, the strategy will enter opposing positions in the pair, in hopes that the price ratio will revert back to the moving average which is when the positions will be exited. The length of the rolling window as well as the thresholds to enter or exit a position can be set.

The performance of this strategy from 2004 can be seen below:
![alt text](https://raw.githubusercontent.com/hugo-chan/Pairs-Trading-Backtest/master/data/pnl.png)

### Limitations of the Strategy
The strategy loses when the price difference between the pair increases from the time of enter and exit.

This may occur when (1) the moving average price ratio changes as a result of historical price movements in the window. The change in the moving average will cause the entry and exit thresholds to change. So even when the price between the two instruments diverges, if the change in the moving average is large enough, the position may be exited at a loss. This problem can be mitigated by reducing the length of the rolling window, but then there may be a tradeoff for increased exposure to short-term noise.

This may also occur when (2) there is a fundamental change in the relationship between the two instruments. This can be seen in the graph during the time of COVID-19, where the strategy creates a large drawdown. The months following March 2020 saw the NASDAQ rallying at a rapid pace, fuelled by the Big Tech stocks, while the S&P 500 posted relatively slower gains. This change in the relationship, where the NASDAQ was growing much quicker, diminished the effectiveness of the moving average in reflecting the fair price ratio between the two instruments. Therefore, the strategy was stuck in a short position on the NASDAQ and a long position on the E-mini and had to wait for the moving average window to catch up to the fundamental change, accumulating a large loss.

### Potential Improvements of the Strategy
Both scenarios described above are related to the accuracy of the rolling moving average in reflecting the current fair ratio between the two instruments. In other words, the current strategy is susceptible to large price movements occuring in either end of the rolling window. This problem can be mitigated by applying a exponential moving average (EMA) instead of a simple moving average (SMA). That way, large price movements at the start of the rolling window will have less of a effect while large price movements at the end of the rolling window will be more effectively captured, more accurately predicting the current fair price ratio between the pair of instruments.


## Built With

* Python (Pandas, NumPy, Matplotlib)
