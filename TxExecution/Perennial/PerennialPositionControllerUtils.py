from perennial_sdk.constants import *
from GlobalUtils.logger import logger
from perennial_sdk.main.markets import *
from APICaller.Perennial.perennialCallerUtils import *
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_position(symbol: str):
    try:
        open_position = GLOBAL_PERENNIAL_CLIENT.account_info.fetch_open_positions(symbol)
        if open_position is None:
            logger.error(f'PerennialPositionControllerUtils - no open positions for {symbol}')
            return None
        return open_position
    except KeyError as e:
        logger.error(f'PerennialPositionControllerUtils - KeyError fetching position for market {symbol}: {e}')
        return None
    except Exception as e:
        logger.error(f'PerennialPositionControllerUtils - Error fetching position for market {symbol}: {e}')
        return None

def get_positions_for_all_markets() -> list:
    try:
        open_positions = []

        with ThreadPoolExecutor() as executor:
            future_to_market = {executor.submit(fetch_position, market_name): market_name for market_name in arbitrum_markets.keys()}
            
            for future in as_completed(future_to_market):
                result = future.result()
                if result is not None:
                    open_positions.append(result)

        if not open_positions:
            logger.error(f'PerennialPositionControllerUtils - No open positions found for any market.')
            return []

        logger.info(f'PerennialPositionControllerUtils - Found {len(open_positions)} open position(s).')
        return open_positions

    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to check for open positions: {e}", exc_info=True)
        return None

def get_pnl_from_the_graph(symbol: str) -> str:
    try:
        account_address = str(os.getenv('ADDRESS'))

        headers = {
            'Content-Type': 'application/json'
        }

        query = """
        query MarketAccountPositions($account: String!) {
            marketAccounts(where: {account: $account}) {
                market {
                    id
                }
                positions(orderBy: nonce, orderDirection: desc) {
                    nonce
                    startVersion
                    accumulation {
                        collateral_subAccumulation_pnl
                        collateral_subAccumulation_funding
                        collateral_subAccumulation_interest
                    }
                }
            }
        }
        """

        variables = {
            "account": account_address
        }

        response = requests.post(arbitrum_graph_url, json={'query': query, 'variables': variables}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            formatted_data = parse_market_account_data(data, symbol)
            return formatted_data
 
    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to fetch MarketAccounts via graph query. Error: {e}", exc_info=True)
        return None

def parse_market_account_data(api_response: dict, symbol: str):
    try:
        market_accounts = api_response.get('data', {}).get('marketAccounts', [])
        
        for account in market_accounts:
            market_id = account.get('market', {}).get('id', None)
            market = get_symbol_for_market_address(market_id)

            if market == symbol and account.get('positions'):
                highest_nonce_position = max(account['positions'], key=lambda pos: int(pos['nonce']))
                
                pnl = highest_nonce_position.get('accumulation', {}).get('collateral_subAccumulation_pnl', '0')
                formatted_pnl = float(pnl) / 1000000
                accrued_funding = highest_nonce_position.get('accumulation', {}).get('collateral_subAccumulation_funding', '0')
                formatted_accrued_funding = float(accrued_funding) / 1000000

                return {
                    "market": market,
                    "pnl": formatted_pnl,
                    "accrued_funding": formatted_accrued_funding
                }
        
        return None

    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to parse market account data. Error: {e}", exc_info=True)
        return None