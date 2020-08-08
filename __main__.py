from src.history import History
from src.plot import plot_cumpnl

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/src")

pairs = [("NASDAQ", "E-MINI")]

for pair in pairs:
    History(pair[0], pair[1])
    plot_cumpnl(pair[0], pair[1])