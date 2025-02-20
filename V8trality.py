#Modded to work with Kraken, change simboles to supported ones,relaxed to be used by everyone

import time

def initialize(state):
    state.signals = {}
    state.cooler = {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'EOSUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'XDGUSDT' : 0 , 'XRPUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'ADAUSDT' : 0,'TRXUSDT': 0}
    state.buyer = {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'EOSUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'XDGUSDT' : 0 , 'XRPUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'ADAUSDT' :0,'TRXUSDT': 0}
    state.tp_newposition =  {'LTCUSDT' : False, 'ADAUSDT' : False, 'EOSUSDT' : False, 'LINKUSDT' : False, 'FIOUSDT' : False, 'XDGUSDT' : False , 'XRPUSDT' : False, 'ETHUSDT' : False, 'DOTUSDT' : False, 'ADAUSDT' : False, 'TRXUSDT':False}
    state.tp_position =  {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'EOSUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'XDGUSDT' : 0 , 'XRPUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'ADAUSDT' : 0,'TRXUSDT': 0}
    state.signal_parameters = [22, 14, 30, 14, 9]
    
SYMBOLS = ["XDGUSDT", "XRPUSDT",  "DOTUSDT", "ADAUSDT"]
SYMBOLS2 = ["EOSUSDT","LTCUSDT","LINKUSDT"]

SIGNAL_BUY = 1
SIGNAL_SELL = 2
SIGNAL_IGNORE = 3



def compute_signal(state, data, short_n, medium_n, long_n, rsi_n, adx_n):
    rsibuy = False
    adxbuy = False
    cross = 0
    orderID = 0
    rsi = data.rsi(14).as_np()[0,:]
    rsi_long = data.rsi(40).as_np()[0,:]
    adx = data.adx(adx_n).as_np()[0,:]
    ema_long = data.ema(long_n).as_np()[0,:]
    ema_short = data.ema(short_n).as_np()[0,:]
    stoch = data.stoch(k_slowing_period=14,k_period=14,d_period=3)
    bbands = data.bbands(20, 2)
    rsishifts = False
    adxshifts = False
    emabuy = False
    stochbuy = False
    if bbands is None:
        return

    bbands_lower = bbands["bbands_lower"].last
    bbands_upper = bbands["bbands_upper"].last
    
    if stoch.stoch_k[0] > stoch.stoch_d[0] and stoch.stoch_k[-1] < stoch.stoch_d[-1] and stoch.stoch_d[0] < 30:
        stochbuy = True

    if  rsi[-1] < rsi[0] < 30:
        rsibuy = True

    if rsi[-2] < rsi[-1] < rsi[0]:
        rsishifts = True
    if adx[-2] < adx[-1] < 25:
        adxbuy = True
    if adx[-2] < adx[-1] < adx[0]:
        adxshifts = True

    if ema_short[-2] < ema_long[-2] and ema_short[-2] > ema_long[-2]:
        cross = 1
    if ema_long[-3] < ema_short[-3] and ema_long[-2] > ema_short[-2]:
        cross = -1

    bbands_adjusted =  (float(bbands_lower) + (float(bbands_lower) * 0.0018)) 
    if ema_short[0] > ema_long[0]:
        emabuy = True
    has_position = has_open_position(data.symbol, include_dust=False)
    portvalue = float(query_portfolio_value())
    portfolio = query_portfolio()
    liquidity = portfolio.excess_liquidity_quoted
    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    worst = portfolio.worst_trade_return * 100
    best = portfolio.best_trade_return * 100
    now = time.time()

############################################################## DEBUG ##################################################################

    if position is not None:
        print(f"● {position.symbol} : Entry Price: {position.entry_price} - Price Now : {data.close_last} - Portofolio : {portvalue} - ADX : {adx[0]} - RSI : {rsi[0]}")

        
########################################################### BUY RULES ##################################################################

    # // Check Liquidity For Buy Rules
    if liquidity > portvalue * 0.48 and position is None:

        if not has_position and stochbuy:
            buy_value = float(portvalue) * 0.48 / data.close_last
            order_market_target(symbol=data.symbol,target_percent=0.48)      
            print(f"● Buy Rule 1 for {data.symbol} , Value: {buy_value} at Current market price: {data.close_last}")
            print(f"● Wallet Value: {portvalue}")
            print(f"● Buy Values - ADX: {adx[0]} // RSI: {rsi[0]} // // TIME DIFF : {now - state.cooler[data.symbol]}")
            buytime = time.time()
            state.buyer[data.symbol] = buytime

        else:
    # // Buy Cooldown
            pass


######################################################### SELL RULES ###################################################################

    if position is not None:
        diff = 100 - ((float(position.entry_price) / float(data.close_last)) * 100)
        if diff >= 0.01 or diff <= -0.01:

            if not state.tp_newposition[data.symbol]:
                if data.close_last >= float(position.entry_price) + (float(position.entry_price) * 0.016):
                    print(f"Position Initiated for {data.symbol} Price: {data.close_last} - Diff: {diff}")
                    state.tp_newposition[data.symbol] = True
                    state.tp_position[data.symbol] = data.close_last
                    
                    
            # // DYNAMIC TP - Stage 2 Every 0.06% And Dynamic STOP LOSS Section.
            elif state.tp_newposition[data.symbol]:
                if data.close_last >= float(state.tp_position[data.symbol]) + (float(position.entry_price) * 0.005):
                    print(f"Position Upgrade for {data.symbol} Price: {data.close_last} - Diff: {diff}")
                    state.tp_position[data.symbol] = data.close_last

             # // DYNAMIC SL - Stop Loss for Position Change -0.03%
                elif data.close_last <= float(state.tp_position[data.symbol]) - (float(position.entry_price) * 0.005):
                    print(f"!!!!!!! STOP LOSS AFTER POSITION CHANGE Initiated for {data.symbol}  Price: {data.close_last} - Diff: {diff} !!!!!!!!!")
                    close_position(data.symbol)
                    state.tp_newposition[data.symbol] = False
                    state.tp_position[data.symbol] = 0
                    selltime = time.time()
                    state.cooler[data.symbol] = selltime


                if data.close_last < float(position.entry_price) - (float(position.entry_price) * 0.1):
                    print(f"STOP LOSS")
                    close_position(data.symbol)
                    state.tp_newposition[data.symbol] = False
                    state.tp_position[data.symbol] = 0
                    selltime = time.time()
                    state.cooler[data.symbol] = selltime


################################################ Cancel Pending Orders Over 300 Seconds #######################################

        try:
            if position is None:
                for order1 in query_open_orders():
                    if data.symbol in order1.symbol:
                        cancel_order(order1.id)
                        print(f"{order1.id} Canceled for {data.symbol}")
        except RuntimeError:
           print(f"Failed to Cancel {order1.id} for {data.symbol}")

############################################# SAVE EMA SIGNAL IN STATE ######################################################

def resolve_ema_signal(state, data):
    if data is None:
        return
    state.signals[data.symbol] = compute_signal(state, data, *state.signal_parameters)

################################################# INTERVALS 1TIK ############################################################

@schedule(interval= "1h", symbol=SYMBOLS, window_size=150)
def handler(state, dataMap):
    for symbol, data in dataMap.items():
        resolve_ema_signal(state, data)

@schedule(interval= "1h", symbol=SYMBOLS2, window_size=150)
def handler2(state, dataMap):
    for symbol, data in dataMap.items():
        resolve_ema_signal(state, data)

############################################################################################################################
