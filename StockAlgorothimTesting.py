import yfinance as yf
import alpaca_trade_api as tradeapi
import json
import websocket
import threading
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.requests import LimitOrderRequest

APCA_API_BASE_URL = 'https://paper-api.alpaca.markets'
APCA_API_KEY_ID = 'INSERT YOUR ALPACA API KEY ID HERE'
APCA_API_SECRET_KEY = 'INSERT YOUR ALPACA API SECRET KEY HERE'
trading_client = TradingClient(APCA_API_KEY_ID, APCA_API_SECRET_KEY)

# Get our account information.
account = trading_client.get_account()

def get_portfolio_assets():
    api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

    try:
        # Get account's positions to fetch all assets in the portfolio
        positions = api.list_positions()
        return positions
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def cancel_all_orders():
    api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

    try:
        # Cancel all open orders
        api.cancel_all_orders()
        print("All open orders have been cancelled.")
    except Exception as e:
        print(f"An error occurred: {e}")

def on_message(ws, message):
    data = json.loads(message)
    print(data)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def start_websocket_stream():
    url = f"wss://paper-api.alpaca.markets/stream"
    headers = {
        "APCA-API-KEY-ID": APCA_API_KEY_ID,
        "APCA-API-SECRET-KEY": APCA_API_SECRET_KEY,
    }

    ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close, header=headers)
    ws.run_forever()

def get_stock_info(symbol):
        stock_info = yf.download(symbol)
        return stock_info

def get_current_price(symbol):
    api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

    try:
        # Get the latest bar data for the stock symbol
        stock_info = api.get_bars(symbol, 'minute', limit=1)[symbol][0]
        current_price = stock_info.c
        return current_price
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def is_price_above_moving_average(symbol, moving_average_days):
    stock_data = yf.download(symbol)
    moving_average = stock_data['Close'].rolling(moving_average_days).mean().iloc[-1]
    current_price = stock_data['Close'].iloc[-1]

    return current_price > moving_average
    
def calculate_rsi(data, period=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def get_stock_rsi(symbol, period=14):
    try:
        stock_data = yf.download(symbol)
        rsi = calculate_rsi(stock_data, period)
        return rsi.iloc[-1]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
        
def is_rsi_above_threshold(symbol, rsi_threshold, period):
    stock_data = yf.download(symbol)
    delta = stock_data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1] > rsi_threshold
    
def is_rsi_below_threshold(symbol, rsi_threshold, period):
    stock_data = yf.download(symbol)
    delta = stock_data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1] < rsi_threshold

def get_highest_rsi(symbol_list, period=10):
    highest_rsi = float('inf')  # Initialize with a high value
    highest_rsi_symbol = None

    for symbol in symbol_list:
        stock_data = yf.download(symbol)
        delta = stock_data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        if current_rsi > highest_rsi:
            highest_rsi = current_rsi
            highest_rsi_symbol = symbol

    return highest_rsi_symbol, highest_rsi

def get_lowest_rsi(symbol_list, period=10):
    lowest_rsi = float('inf')  # Initialize with a high value
    lowest_rsi_symbol = None

    for symbol in symbol_list:
        stock_data = yf.download(symbol)
        delta = stock_data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        if current_rsi < lowest_rsi:
            lowest_rsi = current_rsi
            lowest_rsi_symbol = symbol

    return lowest_rsi_symbol, lowest_rsi

def calculate_cumulative_return(symbol, days):
        stock_data = yf.download(symbol)
        
        # Calculate daily returns
        stock_data['Daily_Return'] = stock_data['Close'].pct_change()

        # Calculate cumulative return for the specified number of days
        stock_data['Cumulative Return'] = (stock_data['Close'].pct_change() + 1).rolling(window=days).apply(lambda x: x.prod(), raw=True)
        return (stock_data['Cumulative Return'].iloc[-1] - 1) * 100  # Convert to percentage

def split_evenly(number):
        number = float(number)
        # Calculate the equal share for each asset
        equal_share = number // 8

        return equal_share

def check_lists_match_all(list1, list2):
    # Find the common elements (intersection) between the two lists
    common_elements = set(list1).intersection(set(list2))

    # Check if the intersection is equal to list2
    return common_elements == set(list2)

if __name__ == "__main__":
    # Start the WebSocket stream in a separate thread
    websocket_thread = threading.Thread(target=start_websocket_stream)
    websocket_thread.daemon = True  # Set the thread as a daemon to exit when the main thread ends
    websocket_thread.start()

    balance_change = float(account.equity) - float(account.last_equity)
    total_balance_change = float(account.equity) - float ("100000")
    portfolio_assets = get_portfolio_assets()
    portfolio_value = float(account.portfolio_value)
    print('${} is available as buying power.'.format(account.buying_power))
    print('${} is available as cash.'.format(account.cash))
    print('')
    print(f'Total Portfolio Value is ${portfolio_value:.2f}')
    print(f'Today\'s portfolio balance change: ${balance_change:.2f}')
    print(f"Total portfolio balance change: ${total_balance_change:.2f}")
    print('')
    if portfolio_assets is not None:
        print("Assets in the portfolio:")
        for position in portfolio_assets:
            print(f"{position.symbol}: {position.qty} shares")

    print('')
    print('Checking if SPY is above 200 MA')
    stock_info = get_stock_info("SPY")
    
    if stock_info is not None:
        twohundredMA = stock_info['Close'].rolling(window=200).mean()
        last_average = twohundredMA.iloc[-1]
        if last_average is not None:
            rounded_average = round(last_average, 2)
            print(f"The two-hundred-day average of SPY is: {rounded_average:.2f}")
        else:
            print(f"The two-hundred-day average of SPY is not available.")

    is_above_ma = is_price_above_moving_average("SPY", 200)
    
    if is_above_ma:
        print(f"The current price of SPY is above its 200 day moving average")
        print("Looking at TQQQ RSI -- Threshold 75 RSI 14 DAY")
        
        #checking TQQQ's 14 day RSI is above 75 
        symbol = "TQQQ"
        rsi_value = get_stock_rsi(symbol)
        rsi_threshold = 75
        is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 14)
        
        print(f"RSI value for {symbol}: {rsi_value:.2f}")

        #Selecting UVXY if TQQQ's 14 day RSI is above 75
        if is_rsi_above:
            symbol = "UVXY"
            print ('RSI is above threshold, selecting UVXY')
            print ('Selling all assets and purchasing UVXY')
            
            #Create market SELL order good for day for each asset in portfolio
            portfolio_assets = get_portfolio_assets()
            cancel_all_orders()
            if portfolio_assets is not None:
                for position in portfolio_assets:
                    print(f"Selling {position.qty} of {position.symbol}")
                    market_order_data = MarketOrderRequest(
                            symbol=position.symbol,
                            qty=position.qty,
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )
                    trading_client.submit_order(
                            order_data=market_order_data
                            )
                    print('Order Submitted')

                #Giving time for order execution        
                time.sleep(10)
                #Canceling all orders to free up buying power
                cancel_all_orders()

            #Create Market buy order for UVXY good for day
            print(f'Buying UXVY with {account.buying_power}')
            market_order_data = MarketOrderRequest(
                            symbol="UVXY",
                            notional=account.buying_power,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
            trading_client.submit_order(
                            order_data=market_order_data
                            )
        #Check 10 day RSI for SPXL
        else:
            print ('RSI is below threshold, checking 10 day RSI for SPXL')
            symbol = "SPXL"
            rsi_value = get_stock_rsi(symbol, 10)
            rsi_threshold = 80
            is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
            print(f"RSI value for {symbol}: {rsi_value:.2f}")

            #Buy UVXY if 10 day RSI is above 80 for SPXL
            if is_rsi_above:
                symbol = "UVXY"
                print ('10 Day RSI of SPXL: is above threshold, selecting UVXY')
                #Create market SELL order good for day for each asset in portfolio
                portfolio_assets = get_portfolio_assets()
                cancel_all_orders()
                if portfolio_assets is not None:
                    for position in portfolio_assets:
                        print(f"Selling {position.qty} of {position.symbol}")
                        market_order_data = MarketOrderRequest(
                                symbol=position.symbol,
                                qty=position.qty,
                                side=OrderSide.SELL,
                                time_in_force=TimeInForce.DAY
                                )
                        trading_client.submit_order(
                                order_data=market_order_data
                                )
                        print('Order Submitted')
                    #Giving time for order execution        
                    time.sleep(10)
                    #Canceling all orders to free up buying power
                    cancel_all_orders()

                #Create Market buy order for UVXY good for day
                print(f'Buying UXVY with {account.buying_power}')
                market_order_data = MarketOrderRequest(
                                symbol="UVXY",
                                notional=account.buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                trading_client.submit_order(
                                order_data=market_order_data
                                )
##################### A BETTER BUY THE DIP ############################################################
            else:
                print ('10 Day RSI of SPXL: is below threshold, selecting \'A better buy the dip\'')
                
                print('First check QQQ\'s 5 day cumalative returns to see if it is below -6%')
                symbol = 'QQQ'               
                cumulative_return_5d = calculate_cumulative_return(symbol, days=5)
                print(f"5-day Cumulative Return for {symbol}: {cumulative_return_5d:.2f}%")
                
                #If below -6%, then check if TQQQ 1 day cumulative return is above 5%
                if cumulative_return_5d < -6:
                    symbol = 'TQQQ'               
                    cumulative_return_1d = calculate_cumulative_return(symbol, days=1)
                    print('5 day cumulative return for QQQ is below -6% threshold')
                    print('Checking TQQQ 1 day cumulative returns')
                    print(f"1-day Cumulative Return for {symbol}: {cumulative_return_1d:.2f}%")

                    #If 1 day cumulative return is greater than 5%, buy SQQQ
                    if cumulative_return_1d > 5:
                        print('1 day cumulative returns is more than 5% - Selecting SQQQ')
                        #Create market SELL order good for day for each asset in portfolio
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')

                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()

                        #Create Market buy order for SQQQ good for day
                        print(f'Buying SQQQ with {account.buying_power}')
                        market_order_data = MarketOrderRequest(
                            symbol="SQQQ",
                            notional=account.buying_power,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
                        trading_client.submit_order(
                            order_data=market_order_data
                            )
                        print('Order Submitted')
                    
                    #If 1 day cumulative return of TQQQ is less than 5%, check if TQQQ 10 day RSI is above 31
                    else:
                        symbol = "TQQQ"
                        rsi_value = get_stock_rsi(symbol, 10)
                        rsi_threshold = 31
                        is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
                        print(f"RSI value for {symbol}: {rsi_value:.2f}")

                        #Buy SQQQ if 10 day RSI of TQQQ is above 31
                        if is_rsi_above:
                            print('RSI is above threshold. Selecting SQQQ')
                            #Create market SELL order good for day for each asset in portfolio
                            portfolio_assets = get_portfolio_assets()
                            cancel_all_orders()
                            if portfolio_assets is not None:
                                for position in portfolio_assets:
                                    print(f"Selling {position.qty} of {position.symbol}")
                                    market_order_data = MarketOrderRequest(
                                            symbol=position.symbol,
                                            qty=position.qty,
                                            side=OrderSide.SELL,
                                            time_in_force=TimeInForce.DAY
                                            )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')

                                #Giving time for order execution        
                                time.sleep(10)
                                #Canceling all orders to free up buying power
                                cancel_all_orders()

                            #Create Market buy order for SQQQ good for day
                            print(f'Buying SQQQ with {account.buying_power}')
                            market_order_data = MarketOrderRequest(
                                symbol="SQQQ",
                                notional=account.buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                            trading_client.submit_order(
                                order_data=market_order_data
                                )
                            print('Order Submitted')
                                    
                        #Buy TQQQ if 10 day RSI of TQQQ is below 31
                        else:
                            print('RSI is below threshold. Selecting TQQQ')
                            #Create market SELL order good for day for each asset in portfolio
                            portfolio_assets = get_portfolio_assets()
                            cancel_all_orders()
                            if portfolio_assets is not None:
                                for position in portfolio_assets:
                                    print(f"Selling {position.qty} of {position.symbol}")
                                    market_order_data = MarketOrderRequest(
                                            symbol=position.symbol,
                                            qty=position.qty,
                                            side=OrderSide.SELL,
                                            time_in_force=TimeInForce.DAY
                                            )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')
                                #Giving time for order execution        
                                time.sleep(10)
                                #Canceling all orders to free up buying power
                                cancel_all_orders()

                            #Create Market buy order for TQQQ good for day
                            print(f'Buying TQQQ with {account.buying_power}')
                            market_order_data = MarketOrderRequest(
                                symbol="TQQQ",
                                notional=account.buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                            trading_client.submit_order(
                                order_data=market_order_data
                                )
                            print('Order Submitted')

                #Ask if QQQ 10 day RSI is above 80
                else:
                    symbol = "QQQ"
                    rsi_value = get_stock_rsi(symbol, 10)
                    rsi_threshold = 80
                    is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
                    print('5-day cumulative return is above -6%')
                    print('Checking if QQQ 10 day RSI is above 80')
                    print(f"RSI value for {symbol}: {rsi_value:.2f}")
                    #Buy SQQQ if QQQ 10 day RSI is above 80
                    if is_rsi_above:
                        print('RSI is above threshold. Selecting SQQQ')
                        #Create market SELL order good for day for each asset in portfolio
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')

                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()

                        #Create Market buy order for SQQQ good for day
                        print(f'Buying SQQQ with {account.buying_power}')
                        market_order_data = MarketOrderRequest(
                            symbol="SQQQ",
                            notional=account.buying_power,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
                        trading_client.submit_order(
                            order_data=market_order_data
                            )
                        print('Order Submitted')

                    #Ask if QQQ is below 31
                    else:
                        symbol = "QQQ"
                        rsi_value = get_stock_rsi(symbol, 10)
                        rsi_threshold = 31
                        is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 10)
                        print('RSI is below threshold, checking if QQQ 10 day RSI is below 31')
                        print(f"RSI value for {symbol}: {rsi_value:.2f}")

                        #If QQQ 10 day RSI is below 31, buy TQQQ
                        if is_rsi_below:
                            print('RSI is below threshold. Selecting TQQQ')
                            #Create market SELL order good for day for each asset in portfolio
                            portfolio_assets = get_portfolio_assets()
                            cancel_all_orders()
                            if portfolio_assets is not None:
                                for position in portfolio_assets:
                                    print(f"Selling {position.qty} of {position.symbol}")
                                    market_order_data = MarketOrderRequest(
                                            symbol=position.symbol,
                                            qty=position.qty,
                                            side=OrderSide.SELL,
                                            time_in_force=TimeInForce.DAY
                                            )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')
                                #Giving time for order execution        
                                time.sleep(10)
                                #Canceling all orders to free up buying power
                                cancel_all_orders()

                            #Create Market buy order for TQQQ good for day
                            print(f'Buying TQQQ with {account.buying_power}')
                            market_order_data = MarketOrderRequest(
                                symbol="TQQQ",
                                notional=account.buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                            trading_client.submit_order(
                                order_data=market_order_data
                                )
                            print('Order Submitted')

                        #If QQQ 10 day RSI is above 31 and below 80, then adopt A Better QQQ
                        ################## A BETTER QQQ STRATEGY #############################
                        else:
                            print('RSI is above threshold. Selecting A better QQQ strategy')
                            #Create market SELL order good for day for each asset in portfolio
                            portfolio_assets = get_portfolio_assets()
                            symbol_list = ["TQQQ", "TSM", "MSFT", "AMZN", "AAPL", "AMD", "NVDA", "TSLA"]
                            if portfolio_assets is not None:
                                if check_lists_match_all([position.symbol for position in portfolio_assets], symbol_list):
                                    print('Already invested in A Better QQQ Strategy')
                                else:
                                    cancel_all_orders()
                                    if portfolio_assets is not None:
                                        for position in portfolio_assets:
                                            print(f"Selling {position.qty} of {position.symbol}")
                                            market_order_data = MarketOrderRequest(
                                                    symbol=position.symbol,
                                                    qty=position.qty,
                                                    side=OrderSide.SELL,
                                                    time_in_force=TimeInForce.DAY
                                                    )
                                            trading_client.submit_order(
                                                    order_data=market_order_data
                                                    )
                                            print('Order Submitted')

                                        #Giving time for order execution        
                                        time.sleep(10)
                                        #Canceling all orders to free up buying power
                                        cancel_all_orders()

                                    asset_shares = split_evenly(account.buying_power)                 
                                    print('Buying 1/8 each of TQQQ, TSM, MSFT, AMZN, AAPL, AMD, NVDA, TSLA')
                                    for symbol in symbol_list:
                                        #Create Market buy order for a better QQQ good for day
                                        print(f'Buying {symbol} with {asset_shares}')
                                        market_order_data = MarketOrderRequest(
                                                        symbol=symbol,
                                                        notional=asset_shares,
                                                        side=OrderSide.BUY,
                                                        time_in_force=TimeInForce.DAY
                                                        )
                                        trading_client.submit_order(
                                                        order_data=market_order_data
                                                        )
                                        print('Order Submitted')
#######################################################################################################################
    else:
        print(f"The current price of SPY is below or equal to its 200-day moving average.")
        print('Checking TQQQ\'s 9 day RSI to see if it is below 32')
        symbol = "TQQQ"
        rsi_value = get_stock_rsi(symbol, 9)
        rsi_threshold = 32
        is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 9)
        print(f"RSI value for {symbol}: {rsi_value:.2f}")

        if is_rsi_below:
            print('9 Day RSI is below threshold, checking if TQQQ 2 day cumulative returns is more than 5 day cumulative returns')
            # Calculate the 2-day and 5-day cumulative returns for TQQQ
            cumulative_return_2d = calculate_cumulative_return(symbol, days=2)
            cumulative_return_5d = calculate_cumulative_return(symbol, days=5)

            if cumulative_return_2d is not None and cumulative_return_5d is not None:
                print(f"2-day Cumulative Return for {symbol}: {cumulative_return_2d:.2f}%")
                print(f"5-day Cumulative Return for {symbol}: {cumulative_return_5d:.2f}%")

                # Ask whether the 2-day cumulative return is above the 5-day cumulative return
                if cumulative_return_2d >= cumulative_return_5d:
                    print("The 2-day cumulative return is above or equal to the 5-day cumulative return.")
                    print('Seleting to go 50/50 on substrategy 1 and 2')
                    print('Selling all assets')
                     #Create market SELL order good for day for each asset in portfolio
                    portfolio_assets = get_portfolio_assets()
                    cancel_all_orders()
                    if portfolio_assets is not None:
                        for position in portfolio_assets:
                            print(f"Selling {position.qty} of {position.symbol}")
                            market_order_data = MarketOrderRequest(
                                    symbol=position.symbol,
                                    qty=position.qty,
                                    side=OrderSide.SELL,
                                    time_in_force=TimeInForce.DAY
                                    )
                            trading_client.submit_order(
                                    order_data=market_order_data
                                    )
                            print('Order Submitted')

                        #Giving time for order execution        
                        time.sleep(10)
                        #Canceling all orders to free up buying power
                        cancel_all_orders()

                    ######## SUB STRATEGY #1 ###################
                    symbol_list = "TECL", "SOXL", "SHY"
                    lowest_rsi_symbol, lowest_rsi = get_lowest_rsi(symbol_list, 10)
                    print(f'The lowest RSI is {lowest_rsi_symbol} with {lowest_rsi:.2f}')
                    fiftypercent = float(account.buying_power) / 2

                    #Market buy 50% of buying power on lowest 10 day RSI between TECL, SOXL, and SHY
                    print(f'Buying {lowest_rsi_symbol} with {fiftypercent:.2f}')
                    market_order_data = MarketOrderRequest(
                    symbol=lowest_rsi_symbol,
                    notional=fiftypercent,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )
                    trading_client.submit_order(
                            order_data=market_order_data
                            )
                    ############################################

                    ######## SUB STRATEGY #2 ###################
                    symbol_list = "SOXL", "SHY"
                    lowest_rsi_symbol, lowest_rsi = get_lowest_rsi(symbol_list, 10)
                    print(f'The lowest RSI is {lowest_rsi_symbol} with {lowest_rsi:.2f}')
                    remainingbuyingpower = account.buying_power

                    #Market buy 50% of buying power on lowest 10 day RSI between SOXL, and SHY
                    print(f'Buying {lowest_rsi_symbol} with {remainingbuyingpower:.2f}')
                    market_order_data = MarketOrderRequest(
                    symbol=lowest_rsi_symbol,
                    notional=remainingbuyingpower,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )
                    trading_client.submit_order(
                            order_data=market_order_data
                            )
                    ############################################
    
                else:
                    print("The 2-day cumulative return is below the 5-day cumulative return.")
                    print('Checking SPY 10 day RSI to see if below 30')
                    symbol = "SPY"
                    rsi_value = get_stock_rsi(symbol, 10)
                    rsi_threshold = 30
                    is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 10)
                    print(f"RSI value for {symbol}: {rsi_value:.2f}")

                    if is_rsi_below:
                        print('RSI is below threshold - Choosing lowest 10 day RSI between SPXL and SHY')
                        symbol_list = "SPXL", "SHY"
                        lowest_rsi_symbol, lowest_rsi = get_lowest_rsi(symbol_list, 10)
                        print(f'The lowest RSI is {lowest_rsi_symbol} with {lowest_rsi:.2f}')

                        #Selling all assets
                        print('Selling all assets')
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')

                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()
                            
                        ##### Buying lowest RSI between SPXL and SHY##########
                        buying_power = account.buying_power
                        print(f'Buying {lowest_rsi_symbol} with {buying_power}')
                        market_order_data = MarketOrderRequest(
                        symbol=lowest_rsi_symbol,
                        notional=buying_power,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
                        trading_client.submit_order(
                                order_data=market_order_data
                                )
                        print('Order Submitted')

                    # Check to see if UVXY 10 day RSI is above 74
                    else:
                        print('Checking UVXY 10 day RSI')
                        symbol = "UVXY"
                        rsi_value = get_stock_rsi(symbol, 10)
                        rsi_threshold = 74
                        is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
                        print(f"RSI value for {symbol}: {rsi_value:.2f}")
                        
                        #Check to see if 10 day RSI is above 84
                        if is_rsi_above:
                            rsi_threshold = 84
                            is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
                            
                            if is_rsi_above:
                                print('RSI is above 84')
                                print('Selecting highest 10 day RSI between BSV and SQQQ')
                                symbol_list = "BSV", "SQQQ"
                                highest_rsi_symbol, highest_rsi = get_highest_rsi(symbol_list, 10)
                                print(f'The highest RSI is {highest_rsi_symbol} with {highest_rsi:.2f}')

                                #Selling all assets
                                print('Selling all assets')
                                portfolio_assets = get_portfolio_assets()
                                cancel_all_orders()
                                if portfolio_assets is not None:
                                    for position in portfolio_assets:
                                        print(f"Selling {position.qty} of {position.symbol}")
                                        market_order_data = MarketOrderRequest(
                                                symbol=position.symbol,
                                                qty=position.qty,
                                                side=OrderSide.SELL,
                                                time_in_force=TimeInForce.DAY
                                                )
                                        trading_client.submit_order(
                                                order_data=market_order_data
                                                )
                                        print('Order Submitted')
                                    #Giving time for order execution        
                                    time.sleep(10)
                                    #Canceling all orders to free up buying power
                                    cancel_all_orders()
                                
                                ##### Buying highest RSI between BSV and SQQQ##########
                                buying_power = account.buying_power
                                print(f'Buying {highest_rsi_symbol} with {buying_power}')
                                market_order_data = MarketOrderRequest(
                                symbol=highest_rsi_symbol,
                                notional=buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')

                            else:
                                print('UVXY 10 day RSI is above 74 but below 84')
                                print('Seleting UVXY')

                                #Selling all assets
                                print('Selling all assets')
                                portfolio_assets = get_portfolio_assets()
                                cancel_all_orders()
                                if portfolio_assets is not None:
                                    for position in portfolio_assets:
                                        print(f"Selling {position.qty} of {position.symbol}")
                                        market_order_data = MarketOrderRequest(
                                                symbol=position.symbol,
                                                qty=position.qty,
                                                side=OrderSide.SELL,
                                                time_in_force=TimeInForce.DAY
                                                )
                                        trading_client.submit_order(
                                                order_data=market_order_data
                                                )
                                        print('Order Submitted')
                                    #Giving time for order execution        
                                    time.sleep(10)
                                    #Canceling all orders to free up buying power
                                    cancel_all_orders()

                                # Market buy UVXY
                                buying_power = account.buying_power
                                print(f'Buying UVXY with {buying_power}')
                                market_order_data = MarketOrderRequest(
                                symbol="UVXY",
                                notional=buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')
                        else:
                            is_above = is_price_above_moving_average("TQQQ", 20)
                            
                            if is_above:
                                print('TQQQ is higher than the 20 day MA, checking if SQQQ RSI is below 31')
                                symbol = "SQQQ"
                                rsi_value = get_stock_rsi(symbol, 10)
                                rsi_threshold = 31
                                is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 10)
                                print(f"RSI value for {symbol}: {rsi_value:.2f}")
                                
                                #Buy SQQQ if SQQQ RSI below 31
                                if is_rsi_below:
                                    print('10 day RSI for SQQQ is below 31')
                                    print('Selecting SQQQ')

                                    #Selling all assets
                                    print('Selling all assets')
                                    portfolio_assets = get_portfolio_assets()
                                    cancel_all_orders()
                                    if portfolio_assets is not None:
                                        for position in portfolio_assets:
                                            print(f"Selling {position.qty} of {position.symbol}")
                                            market_order_data = MarketOrderRequest(
                                                    symbol=position.symbol,
                                                    qty=position.qty,
                                                    side=OrderSide.SELL,
                                                    time_in_force=TimeInForce.DAY
                                                    )
                                            trading_client.submit_order(
                                                    order_data=market_order_data
                                                    )
                                            print('Order Submitted')
                                        
                                        #Giving time for order execution        
                                        time.sleep(10)
                                        #Canceling all orders to free up buying power
                                        cancel_all_orders()

                                    # Market buy SQQQ
                                    buying_power = account.buying_power
                                    print(f'Buying SQQQ with {buying_power}')
                                    market_order_data = MarketOrderRequest(
                                    symbol="SQQQ",
                                    notional=buying_power,
                                    side=OrderSide.BUY,
                                    time_in_force=TimeInForce.DAY
                                    )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')

                                #Buy TQQQ if SQQQ RSI is above 31    
                                else:
                                    print('10 day RSI for SQQQ is above 31')
                                    print('Selecting TQQQ')
                                    #Selling all assets
                                    print('Selling all assets')
                                    portfolio_assets = get_portfolio_assets()
                                    cancel_all_orders()
                                    if portfolio_assets is not None:
                                        for position in portfolio_assets:
                                            print(f"Selling {position.qty} of {position.symbol}")
                                            market_order_data = MarketOrderRequest(
                                                    symbol=position.symbol,
                                                    qty=position.qty,
                                                    side=OrderSide.SELL,
                                                    time_in_force=TimeInForce.DAY
                                                    )
                                            trading_client.submit_order(
                                                    order_data=market_order_data
                                                    )
                                            print('Order Submitted')
                                        
                                        #Giving time for order execution        
                                        time.sleep(10)
                                        #Canceling all orders to free up buying power
                                        cancel_all_orders()

                                    # Market buy TQQQ
                                    buying_power = account.buying_power
                                    print(f'Buying TQQQ with {buying_power}')
                                    market_order_data = MarketOrderRequest(
                                    symbol="TQQQ",
                                    notional=buying_power,
                                    side=OrderSide.BUY,
                                    time_in_force=TimeInForce.DAY
                                    )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')

                            else:
                                print('TQQQ is below 20 day MA')
                                print('Selecting highest 10 day RSI between BSV and SQQQ')
                                symbol_list = "BSV", "SQQQ"
                                highest_rsi_symbol, highest_rsi = get_highest_rsi(symbol_list, 10)
                                print(f'The highest RSI is {highest_rsi_symbol} with {highest_rsi:.2f}')

                                #Selling all assets
                                print('Selling all assets')
                                portfolio_assets = get_portfolio_assets()
                                cancel_all_orders()
                                if portfolio_assets is not None:
                                    for position in portfolio_assets:
                                        print(f"Selling {position.qty} of {position.symbol}")
                                        market_order_data = MarketOrderRequest(
                                                symbol=position.symbol,
                                                qty=position.qty,
                                                side=OrderSide.SELL,
                                                time_in_force=TimeInForce.DAY
                                                )
                                        trading_client.submit_order(
                                                order_data=market_order_data
                                                )
                                        print('Order Submitted')
                                    
                                    #Giving time for order execution        
                                    time.sleep(10)
                                    #Canceling all orders to free up buying power
                                    cancel_all_orders()
                                
                                ##### Buying highest RSI between BSV and SQQQ##########
                                buying_power = account.buying_power
                                print(f'Buying {highest_rsi_symbol} with {buying_power}')
                                market_order_data = MarketOrderRequest(
                                symbol=highest_rsi_symbol,
                                notional=buying_power,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                                )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')

        #If TQQQ 9 day RSI is above 32
        else:
            print('9 day RSI of TQQQ is above 32')
            print('Checking to see if SPY 10 day RSI is below 30')
            symbol = "SPY"
            rsi_value = get_stock_rsi(symbol, 10)
            rsi_threshold = 30
            is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 10)
            print(f"RSI value for {symbol}: {rsi_value:.2f}")

            if is_rsi_below:
                print('SPY RSI is below 32')
                print('Choosing lowest 10 day RSI between SPXL and SHY')
            else:
                print('SPY RSI is above 32')
                print('Checking 10 day RSI for UVXY')
                symbol = "UVXY"
                rsi_value = get_stock_rsi(symbol, 10)
                rsi_threshold = 74
                is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)
                print(f"RSI value for {symbol}: {rsi_value:.2f}")

                if is_rsi_above:
                    rsi_threshold = 84
                    is_rsi_above = is_rsi_above_threshold(symbol, rsi_threshold, 10)

                    if is_rsi_above:
                        print('UVXY RSI is above 84')
                        print('Selecting highest 10 day RSI between BSV and SQQQ')
                        symbol_list = "BSV", "SQQQ"
                        highest_rsi_symbol, highest_rsi = get_highest_rsi(symbol_list, 10)
                        print(f'The highest RSI is {highest_rsi_symbol} with {highest_rsi:.2f}')

                        #Selling all assets
                        print('Selling all assets')
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')
                            
                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()
                        
                        ##### Buying highest RSI between BSV and SQQQ##########
                        buying_power = account.buying_power
                        print(f'Buying {highest_rsi_symbol} with {buying_power}')
                        market_order_data = MarketOrderRequest(
                        symbol=highest_rsi_symbol,
                        notional=buying_power,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
                        trading_client.submit_order(
                                order_data=market_order_data
                                )
                        print('Order Submitted')
                    else:
                        print('UVXY RSI is above 74 but below 84')
                        print('Seleting UVXY')

                        #Selling all assets
                        print('Selling all assets')
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')
                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()

                        # Market buy UVXY
                        buying_power = account.buying_power
                        print(f'Buying UVXY with {buying_power}')
                        market_order_data = MarketOrderRequest(
                        symbol="UVXY",
                        notional=buying_power,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
                        trading_client.submit_order(
                                order_data=market_order_data
                                )
                        print('Order Submitted')

                else:
                    print('UVXY RSI is below 74')
                    print('Checking if TQQQ is above 20 day MA')
                    symbol = "TQQQ"
                    moving_average_days = 20
                    stock_info = get_stock_info(symbol)
                    is_above_ma = is_price_above_moving_average(symbol, moving_average_days)

                    if is_above_ma:
                        print('TQQQ is above 20 day MA')
                        print('Checking if SQQQ 10 day RSI is below 31')
                        symbol = "SQQQ"
                        rsi_value = get_stock_rsi(symbol, 10)
                        rsi_threshold = 31
                        is_rsi_below = is_rsi_below_threshold(symbol, rsi_threshold, 10)
                        print(f"RSI value for {symbol}: {rsi_value:.2f}")
                        
                        #Buy SQQQ if SQQQ RSI below 31
                        if is_rsi_below:
                            print('10 day RSI for SQQQ is below 31')
                            print('Selecting SQQQ')

                            #Selling all assets
                            print('Selling all assets')
                            portfolio_assets = get_portfolio_assets()
                            cancel_all_orders()
                            if portfolio_assets is not None:
                                for position in portfolio_assets:
                                    print(f"Selling {position.qty} of {position.symbol}")
                                    market_order_data = MarketOrderRequest(
                                            symbol=position.symbol,
                                            qty=position.qty,
                                            side=OrderSide.SELL,
                                            time_in_force=TimeInForce.DAY
                                            )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')
                                #Giving time for order execution        
                                time.sleep(10)
                                #Canceling all orders to free up buying power
                                cancel_all_orders()

                            # Market buy SQQQ
                            buying_power = account.buying_power
                            print(f'Buying SQQQ with {buying_power}')
                            market_order_data = MarketOrderRequest(
                            symbol="SQQQ",
                            notional=buying_power,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
                            trading_client.submit_order(
                                    order_data=market_order_data
                                    )
                            print('Order Submitted')

                        #Buy TQQQ if SQQQ RSI is above 31    
                        else:
                            print('10 day RSI for SQQQ is above 31')
                            print('Selecting TQQQ')
                            #Selling all assets
                            print('Selling all assets')
                            portfolio_assets = get_portfolio_assets()
                            cancel_all_orders()
                            if portfolio_assets is not None:
                                for position in portfolio_assets:
                                    print(f"Selling {position.qty} of {position.symbol}")
                                    market_order_data = MarketOrderRequest(
                                            symbol=position.symbol,
                                            qty=position.qty,
                                            side=OrderSide.SELL,
                                            time_in_force=TimeInForce.DAY
                                            )
                                    trading_client.submit_order(
                                            order_data=market_order_data
                                            )
                                    print('Order Submitted')
                                #Giving time for order execution        
                                time.sleep(10)
                                #Canceling all orders to free up buying power
                                cancel_all_orders()

                            # Market buy TQQQ
                            buying_power = account.buying_power
                            print(f'Buying TQQQ with {buying_power}')
                            market_order_data = MarketOrderRequest(
                            symbol="TQQQ",
                            notional=buying_power,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
                            trading_client.submit_order(
                                    order_data=market_order_data
                                    )
                            print('Order Submitted')

                    else:
                        print('TQQQ is below 20 day MA')
                        print('Selecting highest 10 day RSI between BSV and SQQQ')
                        symbol_list = "BSV", "SQQQ"
                        highest_rsi_symbol, highest_rsi = get_highest_rsi(symbol_list, 10)
                        print(f'The highest RSI is {highest_rsi_symbol} with {highest_rsi:.2f}')

                        #Selling all assets
                        print('Selling all assets')
                        portfolio_assets = get_portfolio_assets()
                        cancel_all_orders()
                        if portfolio_assets is not None:
                            for position in portfolio_assets:
                                print(f"Selling {position.qty} of {position.symbol}")
                                market_order_data = MarketOrderRequest(
                                        symbol=position.symbol,
                                        qty=position.qty,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                                        )
                                trading_client.submit_order(
                                        order_data=market_order_data
                                        )
                                print('Order Submitted')
                            #Giving time for order execution        
                            time.sleep(10)
                            #Canceling all orders to free up buying power
                            cancel_all_orders()
                        
                        ##### Buying highest RSI between BSV and SQQQ##########
                        buying_power = account.buying_power
                        print(f'Buying {highest_rsi_symbol} with {buying_power}')
                        market_order_data = MarketOrderRequest(
                        symbol=highest_rsi_symbol,
                        notional=buying_power,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
                        trading_client.submit_order(
                                order_data=market_order_data
                                )
                        print('Order Submitted')