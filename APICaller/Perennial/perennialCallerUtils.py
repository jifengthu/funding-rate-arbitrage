from perennial_sdk.constants.market_addresses import arbitrum_markets
from GlobalUtils.logger import logger
from decimal import Decimal
from perennial_sdk.utils.calc_funding_rate_draft_two import *
from perennial_sdk.sdk import PerennialSDK

GLOBAL_PERENNIAL_CLIENT = PerennialSDK()

def get_market_address_for_symbol(symbol: str) -> str:
    try:
        return arbitrum_markets.get(symbol.lower())
    
    except Exception as e:
        logger.error(f"PerennialCallerUtils - Error fetching market address for symbol {symbol}: {e}")
        return None

def get_symbol_for_market_address(market_address: str) -> str:
    try:
        for symbol, address in arbitrum_markets.items():
            if address.lower() == market_address.lower():
                return symbol

        raise ValueError(f"PerennialCallerUtils - Market address '{market_address}' not found in arbitrum_markets.")

    except Exception as e:
        logger.error(f"PerennialCallerUtils - Error fetching symbol for market address {market_address}: {e}")
        return None

def get_all_symbols() -> list:
    try:
        return list(arbitrum_markets.keys())
    
    except Exception as e:
        logger.error(f"PerennialCallerUtils - Error fetching symbols from arbitrum_markets: {e}")
        return None

def get_funding_velocity_for_symbol(symbol: str, snapshot: dict) -> float:
    try:
        p_controller = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['riskParameter']['pController']
        p_accumulator = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['global']['pAccumulator']
        skew = p_accumulator['_skew']
        big_6_funding_velocity_per_second = Big6Math.div(Decimal(skew), Decimal(p_controller['k']))
        funding_velocity_per_second = float(big_6_funding_velocity_per_second / Decimal(1000000))
        funding_velocity_24hr = funding_velocity_per_second * (3600*24)

        return funding_velocity_24hr
    
    except Exception as e:
        logger.error(f"PerennialCallerUtils - Error fetching funding velocity for symbol {symbol}. Error: {e}", exc_info=True)
        return None

def get_skew_in_asset_for_symbol(symbol: str, snapshot: dict) -> float:
    try:
        long = float(snapshot["result"]["postUpdate"]["marketSnapshots"][0]['nextPosition']['long'] / 1000000)
        short = float(snapshot["result"]["postUpdate"]["marketSnapshots"][0]['nextPosition']['short'] / 1000000)
        if long > short:
            is_skewed_long = True
        else:
            is_skewed_long = False

        if is_skewed_long:
            skew_in_asset = long - short
        else:
            skew_in_asset = short - long
            skew_in_asset = skew_in_asset * -1

        return skew_in_asset
    
    except Exception as e:
        logger.error(f"PerennialCallerUtils - Error fetching market skew for symbol {symbol}. Error: {e}", exc_info=True)
        return None

