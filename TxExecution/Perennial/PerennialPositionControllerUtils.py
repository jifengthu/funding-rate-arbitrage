from perennial_sdk.main.account.account_info import AccountInfo
from perennial_sdk.constants import *
from GlobalUtils.logger import logger

from perennial_sdk.main.markets import *
from APICaller.Perennial.perennialCallerUtils import get_market_address_for_symbol
from perennial_sdk.utils.calc_funding_rate_draft_two import calculate_funding_and_interest_for_sides

from concurrent.futures import ThreadPoolExecutor, as_completed
from perennial_sdk.main.graph_queries.order_fetcher import Order

def fetch_position(market_name):
    try:
        open_position = AccountInfo.fetch_open_positions(market_name)
        logger.info(f'open_position = {open_position}')
        if open_position is None:
            logger.error(f'PerennialPositionControllerUtils - no open positions for {market_name}')
            return None
        return open_position
    except KeyError as e:
        logger.error(f'PerennialPositionControllerUtils - KeyError fetching position for market {market_name}: {e}')
        return None
    except Exception as e:
        logger.error(f'PerennialPositionControllerUtils - Error fetching position for market {market_name}: {e}')
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

def get_pnl_from_the_graph(symbol: str) -> float:
    """Fetch and return the PnL for the given account and market."""
    try:
        account_address = str(os.getenv('ADDRESS'))
        market_address = get_market_address_for_symbol(symbol)
        # snapshot = fetch_market_snapshot([symbol])
        # print_this = snapshot["result"]["postUpdate"]["marketSnapshots"][0]
        # print(print_this)

        headers = {
            'Content-Type': 'application/json'
        }

        query = f"""
        {{
        orderAccumulation(
            first: 1, 
            id: "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
            where: {{ 
                    account: "{account_address}"
                    market: "{market_address}"
                }}
        ) {{
            id
            collateral_accumulation
            fee_accumulation
        }}
        }}
        """



        response = requests.post(arbitrum_graph_url, json={'query': query}, headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                print(data)
                order = data['data']['orderAccumulation']

                order_obj = {
                    'order_id': order['id'],
                    'account': order['account'],
                    'market': f"{symbol} ({order['market']})",
                    'side': "Long" if order['triggerOrderSide'] == 1 else "Short",
                    'trigger_price': f"{int(order['triggerOrderPrice']) / 1e6:.2f}",  # Price in micro units
                    'trigger_delta': f"{int(order['triggerOrderDelta']) / 1e6:.4f}",  # Delta in micro units
                    'comparison': "<=" if order['triggerOrderComparison'] == -1 else ">=",
                    'cancelled': order['cancelled'],
                    'executed': order['executed'],
                    'collaterals': order['associatedOrder'],
                    'nonce': order['nonce']
                }

                return order_obj
            
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"PerennialPositionControllerUtils - Failed to parse response as JSON. Error: {e}, Raw response: {response.text}", exc_info=True)
                return None

    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to fetch PnL via graph query. Error: {e}", exc_info=True)
        return None

def get_market_accounts(symbol: str) -> str:
    try:
        account_address = str(os.getenv('ADDRESS'))
        market_address = get_market_address_for_symbol(symbol)

        headers = {
            'Content-Type': 'application/json'
        }

        query = f"""
        {{
        marketAccounts(
            where: {{ 
                    account: "{account_address}"
                    market: "{market_address}"
                }}
        )
        }}
        """

        response = requests.post(arbitrum_graph_url, json={'query': query}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(data)
            order = data['data']['orderAccumulation']
            print(order)

    
    except Exception as e:
        logger.error(f"PerennialPositionControllerUtils - Failed to fetch MarketAccounts via graph query. Error: {e}", exc_info=True)
        return None

x = get_market_accounts('eth')
print(x)