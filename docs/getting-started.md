Once you have cloned the repo and installed all dependencies navigate to the .env file and input the necessary values. You will need:

- An Alchemy API key (Base + Arbitrum)
- The relevant chainId (Base Mainnet: 8453, Base Testnet: 84532)
- Your wallet address and Private Key (For security reasons you should create a new wallet to use here)

Some recommended values for the following vars are as follows:
- `TRADE_LEVERAGE=5`
- `DELTA_BOUND=0.03`
- `PERCENTAGE_CAPITAL_PER_TRADE=50`

The vars:
- `DEFAULT_TRADE_DURATION_HOURS=8`
and
- `DEFAULT_TRADE_SIZE_USD=250`
are there for determining the most profitable opportinity. The actual size of your trades will be determined by how much collateral is in your accounts, the leverage factor, and the percentage capital per trade.

Trade Leverage specifies the leverage applied to the collateral amount on each trade. Setting this value too high will result in positions being liquidated, so keeping a relatively small cap is a good idea.
Delta Bound calculates the maximum delta on a trade pair before it will be cancelled by the health checker. The delta between positions will in most cases be 0.0, so this is mostly a failsafe.
Percentage Capital Per Trade specifies the amount of available capital to be used on each trade that is executed. This is derived by checking how much available collateral there is on each exchange, then taking the smaller value and calculating `(smallerValue/100)*PERCANTAGE_CAPITAL_PER_TRADE`. Higher values for this will of course make the trade sizes larger, and therefore will mean having to rebalance the collateral between exchanges more frequently.

In addition, you can choose which tokens to target/exclude from the searching algorithm via navigating to `APICaller.master.MasterUtils.py`, where you will find an array that looks like this:
```python
TARGET_TOKENS = [
    {"token": "BTC", "is_target": True},
    {"token": "ETH", "is_target": True},
]
```
To include/exclude a token, simply replace `True` with `False` and vice versa. The above example targets both BTC and ETH, but if for the sake of argument we only wanted to target ETH, we'd edit the array to look like the following:
```python
TARGET_TOKENS = [
    {"token": "BTC", "is_target": False},
    {"token": "ETH", "is_target": True},
]
```
The bot will now only target ETH opportunities.

To switch between which exchanges are targeted, there is a similar array:
```python
TARGET_EXCHANGES = [
    {"exchange": "GMX", "is_target": True},
    {"exchange": "Synthetix", "is_target": True},
]
```
**It's currently recommended that you run with exchanges GMX, Synthetix, and ByBit.**
Note that some additional steps are required before executing trades, namely that a Synthetix perps account will have to be created and have some collateral deployed. The code for this is found in the next section.

## Testnet config
To start executing some test trades, first you will need to mint some fUSDC on Base sepolia (you can do that [here](https://sepolia.basescan.org/address/0xa1ae612e07511a947783c629295678c07748bc7a#writeContract) by calling `deposit_eth` with some testnet Eth and '0xc43708f8987Df3f3681801e5e640667D86Ce3C30' as the token_address argument). 
After you have some fUSDC, you can call the collateral deposit function by running the `deploy-collateral` command in the CLI. Once you click enter it will ask you for the amount to deposit. Amount is denominated in USD, so to deposit 100 USDC, you'd enter the command as follows:
`
deploy-collateral 100 
`

For the Binance side, you will have to create an account and set of API keys [here](https://testnet.binancefuture.com/en/futures/BTCUSDT), and use these keys in the .env file. Additionally, whether the Binance client is set to testnet or live trading is determined upon initialisation of the Binance clients. By default they will target testnet and look like so:

```python
self.client = Client(api_key, api_secret, base_url="https://testnet.binancefuture.com")
```

To switch to live trading, simply remove the final argument like so:

```python
self.client = Client(api_key, api_secret)
```

> As of version 0.3.0, there are Binance clients initialised in the following files. Make sure all are configured uniformly.
    - BinanceCaller.py
    - BinancePositionController.py
    - BinancePositionMonitor.py
