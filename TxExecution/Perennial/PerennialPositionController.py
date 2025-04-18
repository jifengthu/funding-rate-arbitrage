from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from perennial_sdk.config import *
from perennial_sdk.main.orders.order_manager import *
import time
from TxExecution.Perennial.PerennialPositionControllerUtils import *
from APICaller.Perennial.perennialCallerUtils import *


class PerennialPositionController:
    def __init__(self):
        self.leverage = int(os.getenv('TRADE_LEVERAGE'))
        self.client = GLOBAL_PERENNIAL_CLIENT

    def execute_trade(self, opportunity: dict, is_long: bool, trade_size: float):
        try:
            symbol = str(opportunity['symbol']).lower()
            trade_size_with_leverage = trade_size * self.leverage
            price = get_price_coingecko(SYMBOL_COINGECKO_MAP[symbol.upper()])
            trade_size_asset = trade_size_with_leverage / price
            collateral_amount = get_arbitrum_usdc_balance_global()
            if is_long == True:
                long_amount = trade_size_asset
                short_amount = 0
            else:
                long_amount = 0
                short_amount = trade_size_asset
            
            
            signed_tx_hash_commit = self.client.tx_executor.commit_price_to_multi_invoker(symbol.lower())
            if not is_transaction_hash(signed_tx_hash_commit):
                logger.error(f'PerennialPositionController - Failed to execute a trade for {symbol}; No transaction hash returned from committing price to multi invoker.')
                return None
            
            logger.info(f'long_amount = {long_amount}')
            logger.info(f'short_amount = {short_amount}')
            logger.info(f'collateral_amount = {collateral_amount}')

            signed_tx_hash_place_market_order = '0x' + self.client.tx_executor.place_market_order(
                symbol, 
                long_amount, 
                short_amount, 
                0, 
                int(collateral_amount)
            )

            if not is_transaction_hash(signed_tx_hash_place_market_order):
                logger.error(f'PerennialPositionController - Failed to execute a trade for {symbol}; No transaction hash returned from market order.')
                return None
            
            time.sleep(10)
            if self.was_position_opened_successfully(
                symbol,
                is_long
            ):
                logger.info(f"PerennialPositionController - Trade executed: symbol={symbol} side={'Long' if is_long else 'Short'}, Size USD={trade_size_with_leverage}")
                try:
                    position_object = self.get_position_object(
                    opportunity,
                    is_long,
                    trade_size_with_leverage
                    )
                    return position_object
                except Exception as ie:
                    logger.error(f"PerennialPositionController - Failed to build position object, despite trade executing successfully for symbol {symbol}. Error: {ie}")
                    return None 
            else:
                logger.info("PerennialPositionController - Order not filled after 10 seconds.")
                return None

        except Exception as e:
            logger.error(f'PerennialPositionController - Failed to execute trade for symbol {symbol}. Error: {e}', exc_info=True)
            return None

    def close_position(self, symbol: str, reason: str = None):
        try:
            position = self.get_open_position_for_symbol(symbol)
            if position['is_long'] == True:
                is_long = True
            else:
                is_long = False

            tx_hash_commit = self.client.tx_executor.commit_price_to_multi_invoker(symbol)
            if not is_transaction_hash(tx_hash_commit):
                logger.error(f'PerennialPositionController - Failed to commit price to multi invoker for {symbol}; No transaction hash returned from market order.')
                return None
            logger.info(f"PerennialPositionController - Commit price transaction Hash: 0x{tx_hash_commit}")

            tx_hash_update = self.client.tx_executor.close_position_in_market(symbol)
            if not is_transaction_hash(tx_hash_update):
                logger.error(f'PerennialPositionController - Failed to close position for {symbol}; No transaction hash returned from market order.')
                return None
            logger.info(f"PerennialPositionController - Close position transaction Hash: {tx_hash_update}")

            time.sleep(10)

            tx_hash_withdraw = self.client.tx_executor.withdraw_collateral(symbol)
            if not is_transaction_hash(tx_hash_update):
                logger.error(f'PerennialPositionController - Failed to close position for {symbol}; No transaction hash returned from market order.')
                return None
            logger.info(f"PerennialPositionController - Withdraw collateral transaction Hash: {tx_hash_withdraw}")


            time.sleep(10)
            if not self.was_position_closed_successfully(symbol, is_long):
                logger.error(f'PerennialPositionController - Position not closed after 10 second delay.')
                return None

            pnl_dict = get_pnl_from_the_graph(symbol)
            position_close_object = self.build_position_closed_object(symbol, reason, pnl_dict)
            self.handle_position_closed(position_close_object)
        
        except Exception as e:
            logger.error(f"PerennialPositionController - Error closing position for {symbol}. Error: {e}", exc_info=True)
            return None

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_available_collateral(self) -> float:
        try:
            usdc_balance = get_arbitrum_usdc_balance_global()
            return usdc_balance
        
        except Exception as e:
            logger.error(f"PerennialPositionController - Error getting available USDC balance from smart contract. Error: {e}")
            return None

    def was_position_opened_successfully(self, symbol: str, is_long: bool) -> bool:
        try:
            open_positions = self.get_open_positions()

            for position in open_positions:
                position_symbol = position['market_symbol'][0]
                position_is_long = position['is_long']
                
                if position_symbol == symbol and position_is_long == is_long:
                    return True

            return False
        except Exception as e:
            logger.error(f"PerennialPositionController - Error checking if position was opened successfully for {symbol}. Error: {e}")
            return False
    
    def was_position_closed_successfully(self, symbol: str, is_long: bool) -> bool:
        try:
            open_positions = self.get_open_positions()
            if len(open_positions) == 0:
                return True

            for position in open_positions:
                position_symbol = position['market']
                position_is_long = True if position['side'].lower() == 'long' else False
                
                if position_symbol == symbol and position_is_long == is_long:
                    if position['position_size'] != 0:
                        return False

            logger.info(f'PerennialPositionController - No conditions met while checking if position closed, returning True')
            return True
        except Exception as e:
            logger.error(f"PerennialPositionController - Error checking if position was opened successfully for {symbol}. Error: {e}")
            return False
        
    def handle_position_closed(self, close_position_details: dict):
        try:
            pub.sendMessage(topicName=EventsDirectory.POSITION_CLOSED.value, position_report=close_position_details)
            return 
        except Exception as e:
            logger.error(f"PerennialPositionController - Failed to handle position closed with details: {close_position_details}. Error: {e}")
            return None

    def get_open_positions(self) -> list:
        try:
            positions = get_positions_for_all_markets()
            if not positions:
                logger.error(f"PerennialPositionController - Failed to get open positions, None value returned from get_positions_for_all_markets")
                return None
            if len(positions) > 0:
                return positions
            else:
                return None

        except Exception as e:
            logger.error(f"PerennialPositionController - Failed to get open positions: {e}", exc_info=True)
            return None

    def get_open_position_for_symbol(self, symbol: str) -> dict:
        try:
            positions = self.get_open_positions()
            for position in positions:
                position_symbol = get_symbol_for_market_address(position['market'])
                
                if position_symbol == symbol:
                    return position
                else:
                    continue
            
            return None

        except Exception as e:
            logger.error(f"PerennialPositionController - Failed to get open position for symbol {symbol}. Error: {e}", exc_info=True)
            return None

    def is_already_position_open(self) -> bool:
        try:
            positions = self.get_open_positions()
            if positions == None:
                return False
            if len(positions) > 0:
                return True
            else:
                return False

        except KeyError as ke:
            logger.error(f"PerennialPositionController - KeyError while checking if position is open: {ke}")
            return None
        except TypeError as te:
            logger.error(f"PerennialPositionController - TypeError while checking if position is open: {te}")
            return None
        except Exception as e:
            logger.error(f"PerennialPositionController - Error while checking if position is open: {e}", exc_info=True)
            return None
    
    def get_position_object(self, opportunity: dict, is_long: bool, size_usd: float) -> dict:
        try:
            symbol = opportunity['symbol']
            side = 'Long' if is_long else 'Short'
            liquidation_price = self.client.account_info.get_liquidation_price_for_position(symbol)

            return {
                'exchange': 'Perennial',
                'symbol': symbol,
                'side': side,
                'size': size_usd,
                'liquidation_price': liquidation_price
            }
        
        except Exception as e:
            logger.error(f"PerennialPositionController - Failed to generate position object for {symbol}. Error: {e}", exc_info=True)
            return None
    
    def build_position_closed_object(self, symbol: str, reason: str, pnl: dict) -> dict:
        try:
            if reason == None:
                reason = 'TEST'
            
            pnl_number = pnl['pnl']
            accrued_funding = pnl['accrued_funding']

            close_position_details = {
                'symbol': symbol,
                'exchange': 'Perennial',
                'pnl': pnl_number,
                'accrued_funding': accrued_funding,
                'reason': reason
            }

            return close_position_details

        except Exception as e:
            logger.error(f"PerennialPositionController - Failed to handle position closed with details: {close_position_details}. Error: {e}", exc_info=True)
            return None

