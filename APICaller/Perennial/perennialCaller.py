from GlobalUtils.logger import *
from APICaller.Perennial.perennialCallerUtils import *
from perennial_sdk.main.markets.market_info import MarketInfo, fetch_market_snapshot
import json

class PerennialCaller:
    def __init__(self):
        return

    def get_funding_rates(self, symbols: list):
        try:
            funding_rates = {}
            snapshots = {}
            for symbol in symbols:
                if symbol == 'meem':
                    continue
                snapshot = fetch_market_snapshot([symbol])
                snapshots[symbol] = snapshot
                symbol = symbol.lower()
                if symbol == 'msqbtc':
                    symbol = 'msqBTC'
                if symbol == 'cmsqeth':
                    symbol = 'cmsqETH'
                client = MarketInfo(symbol)
                funding_rate_data = client.fetch_market_funding_rate(symbol, snapshot)
                funding_rates[symbol] = funding_rate_data
            
            filtered_rates = self._filter_market_data(funding_rates, symbols, snapshots)

            return filtered_rates
        except Exception as e:
            logger.error(f"PerennialAPICaller - Error fetching market data for symbol {symbol}. Error: {e}", exc_info=True)
            return []

    def _filter_market_data(self, funding_rate_data: dict, symbols: list, snapshots: dict):
        market_funding_rates = []
        for symbol in symbols:
            if symbol in funding_rate_data:
                try:
                    market_data = funding_rate_data[symbol]
                    funding_rate_24 = (market_data['net_rate_long_1hr'] / 100) * 24
                    index_price = MarketInfo(symbol).fetch_market_price(snapshots[symbol])
                    skew_in_asset = get_skew_in_asset_for_symbol(symbol, snapshots[symbol])
                    skew_usd = skew_in_asset * index_price
                    funding_velocity = get_funding_velocity_for_symbol(symbol, snapshots[symbol])
                    funding_rate = funding_rate_24 / 3 
                    symbol = symbol.upper()
                    market_funding_rates.append({
                        'exchange': 'Perennial', 
                        'symbol': symbol,
                        'funding_rate': funding_rate,
                        'funding_velocity': funding_velocity,
                        'skew_usd': skew_usd
                    })
                except KeyError as e:
                    logger.error(f"PerennialAPICaller - Error processing market data for {symbol}: {e}")
        return market_funding_rates

# x = PerennialCaller()
# symbols = get_all_symbols()
# if 'mog' in symbols:
#     symbols.remove('mog')

# y = x.get_funding_rates(['eth'])
# logger.info(y)
# with open('perennialTest.json', 'w') as f:
#     json.dump(y, f, indent=4)