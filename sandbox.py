from datetime import timedelta, datetime

import ta
from ta import volatility, trend, momentum
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt

from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest import MoneyValue, Client, OrderDirection, OrderType, CandleInterval
from tinkoff.invest.services import InstrumentsService

import creds


account_id = '2a3ccaf8-bfb9-44b5-9bef-31ffa9a1676b'


def cast_money(v):
    return v.units + v.nano*10**-9


def get_all_events():
    with SandboxClient(creds.sandbox) as client:
        instruments = client.instruments
        active = []
        for method in ['shares', 'bonds', 'etfs']:
            for item in getattr(instruments, method)().instruments:
                active.append({
                    'name': item.name,
                    'ticker': item.ticker,
                    'figi': item.figi,
                    'currency': item.currency,
                    'trading status': item.trading_status,
                    'sector': item.sector
                    })

    return active


def search_event(t):
    df = pd.DataFrame(get_all_events())
    df = df[df['ticker'] == t]
    if df.empty:
        print("404")
        return

    #print(df.iloc[0])
    return df


def get_portfolio():
    with SandboxClient(creds.sandbox) as cl:
        return cl.operations.get_portfolio(account_id=account_id)


def get_sandbox_accounts():
    with SandboxClient(creds.sandbox) as cl:
        return cl.users.get_accounts().accounts


def get_orders():
    with SandboxClient(creds.sandbox) as cl:
        return cl.orders.get_orders(account_id=account_id)


def pay_in(units=100000, nano=0, currency='rub'):
    with SandboxClient(creds.sandbox) as cl:
        return cl.sandbox.sandbox_pay_in(account_id=account_id,
                                         amount=MoneyValue(units=units, nano=nano, currency=currency))


def buy(figi, quantity=1):
    with SandboxClient(creds.sandbox) as cl:
        return cl.orders.post_order(
            figi=figi,
            quantity=quantity,
            account_id=account_id,
            order_id=datetime.now().strftime("%Y-%m-%dT %H:%M:%S"),
            direction=OrderDirection.ORDER_DIRECTION_BUY,
            order_type=OrderType.ORDER_TYPE_MARKET
        )


def print_positions():
    [print(i.figi,
           i.quantity.units+i.quantity.nano*10**-9,
           i.average_position_price.units+i.average_position_price.nano*10**-9,
           i.average_position_price.currency)
     for i in get_portfolio().positions]


def create_df(candles):
    df = DataFrame([{
        'time': c.time,
        'volume': c.volume,
        'open': cast_money(c.open),
        'close': cast_money(c.close),
        'high': cast_money(c.high),
        'low': cast_money(c.low),
    } for c in candles])
    return df


def graf(figi):
    with SandboxClient(creds.sandbox) as cl:
        r = cl.market_data.get_candles(
            figi=figi,
            from_=datetime.utcnow() - timedelta(days=365),
            to=datetime.utcnow(),
            interval=CandleInterval.CANDLE_INTERVAL_DAY # см. utils.get_all_candles
        )
    df = create_df(r.candles)
    df = ema(df)
    df = macd_12_26_9(df)
    print(df['macd'].values[-1])
    plt.plot(df['time'], df['macd'], color='green')
    plt.plot(df['time'], df['signal'], color='orange')
    plt.show()


def macd_12_26_9(df):
    df['ma_fast'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ma_slow'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ma_fast'] - df['ma_slow']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df


def ema(df):
    df['ema'] = ta.trend.ema_indicator(close=df['close'], window=9)
    return df


def print_df(df):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df)


def main():

    graf('BBG004731032')
    print(search_event('LKOH')['figi'].values[0])


if __name__ == "__main__":
    main()
