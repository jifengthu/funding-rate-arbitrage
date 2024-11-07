from perennial_sdk.main.markets.market_info import fetch_market_snapshot
from perennial_sdk.utils.calc_funding_rate_draft_two import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *


def calculate_new_funding_velocity_perennial(symbol: str, trade_size_usd: float, is_long: bool) -> float:
    try:
        snapshot = fetch_market_snapshot([symbol])
        price = snapshot["result"]["postUpdate"]["marketSnapshots"][0]["global"]["latestPrice"] / 1e6
        p_controller = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['riskParameter']['pController']
        long = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['nextPosition']['long']
        short = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['nextPosition']['short']
        maker = Decimal(snapshot["result"]["postUpdate"]["marketSnapshots"][0]['nextPosition']['maker'])
        efficiency_limit = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['riskParameter']['efficiencyLimit']
        utilization_curve = snapshot["result"]["postUpdate"]["marketSnapshots"][0]['riskParameter']['utilizationCurve']
        size_in_asset = trade_size_usd / price
        long = float(long) / 10**6
        short = float(short) / 10**6
        if is_long:
            long = long + size_in_asset
        else:
            short = short + size_in_asset

        new_skew = (long - short) / max(long, short)

        big_6_funding_velocity_per_second = Big6Math.div(Decimal(new_skew * 1000000), Decimal(p_controller['k']))
        funding_velocity_per_second = float(big_6_funding_velocity_per_second / Decimal(1000000))
        funding_velocity_24hr = funding_velocity_per_second * (3600*24) * 100

        major = Big6Math.max(Decimal(long), Decimal(short))
        minor = Big6Math.min(Decimal(long), Decimal(short))

        net_utilization = Big6Math.div(major, maker + minor) if (maker + minor) > 0 else Big6Math.ZERO
        efficiency_utilization = Big6Math.mul(major, Big6Math.div(efficiency_limit, maker)) if maker > 0 else 100 * Big6Math.ONE
        utilization = Big6Math.min(100 * Big6Math.ONE, Big6Math.max(net_utilization, efficiency_utilization))
        interest_rate = float(compute_interest_rate(utilization_curve, utilization)) / 1000000


        return funding_velocity_24hr / 10000

    except Exception as e:
        logger.error(f'PerennialPositionController - Failed to execute trade for symbol {symbol}. Error: {e}', exc_info=True)
        return None

def calculate_profit_perennial(absolute_size_usd: float, time_period_hours: float, funding_velocity_24h: float, initial_funding_rate_24h: float) -> float:
    try:
        funding_change_per_hour = (funding_velocity_24h / 24)
        final_funding_rate = initial_funding_rate_24h + (funding_change_per_hour * time_period_hours)
        average_daily_funding_rate = (initial_funding_rate_24h + final_funding_rate) / 2
        profit_per_day = abs(average_daily_funding_rate) * absolute_size_usd
        days = time_period_hours / 24
        profit = abs(profit_per_day * days)

        return profit
    
    except Exception as e:
        logger.error(f'GMXCheckProfitabilityUtils - Error estimating profit via average rate for period, size_usd = {absolute_size_usd}, time_period_hours = {time_period_hours}, funding_velocity_24h = {funding_velocity_24h}, initial_funding_rate = {initial_funding_rate_24h}: {e}')
        return None

def estimate_time_to_neutralize_rate_perennial(opportunity: dict, absolute_size_usd: float) -> float:
    try:
        symbol = opportunity['symbol']
        
    except Exception as e:
        logger.error(f'GMXCheckProfitabilityUtils - Error estimating time to neutrlize rate for symbol {symbol}. Error: {e}')
        return None