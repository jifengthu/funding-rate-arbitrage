from GlobalUtils.logger import *
from APICaller.Perennial.perennialCallerUtils import *
from perennial_sdk.main.markets.market_info import MarketInfo, fetch_market_snapshot
from concurrent.futures import ThreadPoolExecutor


class PerennialCaller:
    def __init__(self):
        self.client = GLOBAL_PERENNIAL_CLIENT

    def get_funding_rates(self, symbols: list):
        try:
            funding_rates = {}
            snapshots = fetch_market_snapshot([symbols])

            for symbol in symbols:
                if symbol == 'meem':
                    continue

                snapshot = snapshots.get(symbol)
                if not snapshot:
                    logger.warning(f"Snapshot not found for symbol: {symbol}")
                    continue

                symbol_key = symbol.lower()
                if symbol_key == 'msqbtc':
                    symbol_key = 'msqBTC'
                if symbol_key == 'cmsqeth':
                    symbol_key = 'cmsqETH'

                funding_rate_data = self.client.market_info.fetch_market_funding_rate(symbol_key, snapshot)
                funding_rates[symbol_key] = funding_rate_data

            filtered_rates = self._filter_market_data(funding_rates, symbols, snapshots)

            return filtered_rates

        except Exception as e:
            logger.error(f"PerennialAPICaller - Error fetching market data for symbols. Error: {e}", exc_info=True)
            return []


    def _filter_market_data(self, funding_rate_data: dict, symbols: list, snapshots: dict):
        try:
            market_funding_rates = []
            for symbol in symbols:
                if symbol in funding_rate_data:
                    try:
                        market_data = funding_rate_data[symbol]
                        funding_rate_24 = (market_data['net_rate_long_1hr'] / 100) * 24
                        index_price = MarketInfo(symbol).fetch_market_price(snapshots[symbol])
                        skew_in_asset = get_skew_in_asset_for_symbol(symbol, snapshots[symbol])
                        skew_usd = skew_in_asset * index_price
                        if skew_usd == 0.0:
                            continue
                        if skew_usd == -0.0:
                            continue
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
        
        except Exception as e:
            logger.error(f"PerennialAPICaller - Error parsing market data for symbols. Error: {e}", exc_info=True)
            return []

