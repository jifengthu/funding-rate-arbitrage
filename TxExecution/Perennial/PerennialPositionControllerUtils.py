from perennial_sdk.main.account.account_info import AccountInfo
from perennial_sdk.constants import *
from GlobalUtils.logger import logger

from perennial_sdk.main.markets import *
from APICaller.Perennial.perennialCallerUtils import get_market_address_for_symbol
from perennial_sdk.utils.calc_funding_rate_draft_two import calculate_funding_and_interest_for_sides


def get_positions_for_all_markets() -> list:
    try:
        open_positions = []

        for market_name, market_address in arbitrum_markets.items():
            try:
                open_position = AccountInfo.fetch_open_positions(market_name)
            except KeyError as e:
                logger.error(f'PerennialPositionControllerUtils - KeyError fetching position for market {market_name}: {e}')
                continue

            if open_position:
                open_positions.append(open_position)

        if len(open_positions) > 0:
            logger.info(f'PerennialPositionControllerUtils - Found {len(open_positions)} open position(s):')
            return open_positions
        else:
            logger.info(f'PerennialPositionControllerUtils - No open positions found for wallet.')
            return []
    
    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to check for open positions: {e}", exc_info=True)
        return None

