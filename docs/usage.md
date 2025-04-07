# Usage

## CLI Commands
- **`project-run`**: Start the bot.
- **`project-run-demo`**: Search opportunities without executing trades
- **`deploy-collateral-synthetix [amount]`** Deposit collateral to Synthetix
- **`deploy-collateral-gmx [amount]`** Deposit collateral to GMX

### Switching networks
Edit `.env`
   
   - Testnet `CHAIN_ID=84532`
   - Mainnet: `CHAIN_ID=8453`

### Configuring Tokens
Modify `APICaller/master/MasterUtils.py`:

```python
TARGET_TOKENS = [
    {"token": "BTC", "is_target": True},
    {"token": "ETH", "is_target": False},
]
```


