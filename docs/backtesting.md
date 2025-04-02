## Backtesting

New module introduced in v0.2.0 - fetches, parses, and runs backdated strategies on any asset in the `TARGET_TOKENS` enum. Some helper functions are included, mainly to abstract away the process of calling the `MarketProxy` contract for historical funding rate data. This is done in one call, and sorted by asset + block number before being written to local storage in the relevant JSON file. Upon analysis, this data is parsed into pandas DataFrames which makes running the tests easier - The current model runs for one asset at a time, entering a position when the discrepancy in funding rates rises above a given bound, and closes the position when it falls back below.

From some initial runs, we find a handful of useful results:
![Funding Rate Differential](Assets/SNXvBinance.png)
First of all that the funding rate on the Synthetix market is much more volatile than the Binance equivalent, which tells us that we will in most cases be taking the Synthetic position as the 'yield farm' and the Binance position as the hedge.

A visualisation of the strategy would look like the following:
![Backtest Results](Assets/backtest1.png)
We see that the strategy is generally functioning well, but shows that there are many optimisations that we can make. Timing the trade to get out before the funding rate flips, and therefore avoiding some of the `taker` fees in favour of the lower `maker` fees. This part of the repo is free to play around with, and tinkering with strategies, leverage numbers, entry and exit conditions is highly encouraged.
