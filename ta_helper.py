from datetime import timedelta, datetime

import creds
import ta
from ta import volatility, trend, momentum
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import mplfinance as mpf

from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest import MoneyValue, Client, OrderDirection, OrderType, CandleInterval
from tinkoff.invest.services import InstrumentsService

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"

import api

import os
import json
import requests
from bs4 import BeautifulSoup
import time


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
                    'method': method,
                    'figi': item.figi,
                    'isin': item.isin,
                    'currency': item.currency,
                    'trading status': item.trading_status,
                    'sector': item.sector
                    })

    return active


def search_event(t):
    df = pd.DataFrame(get_all_events())
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', None)
    # print(df)
    df = df[df['ticker'] == t]
    if df.empty:
        print("404")
        return
    return df


def candles(figi, days, interval):
    with SandboxClient(creds.sandbox) as cl:
        print(cl)
        r = cl.market_data.get_candles(
            figi=figi,
            from_=datetime.utcnow() - timedelta(days=days),
            to=datetime.utcnow(),
            interval=interval
        )
    return r


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


def table(figi, days=120, interval=CandleInterval.CANDLE_INTERVAL_DAY):
    df = create_df(candles(figi, days, interval).candles)
    print(df)
    df = ema(df)
    df = macd_12_26_9(df)
    return df


def graf(df, event):

    df.set_index('time', inplace=True)  # Установка столбца 'time' в качестве индекса

    exp12 = df['close'].ewm(span=12, adjust=False).mean()
    exp26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    fb_12up = dict(y1=exp12.values, y2=exp26.values, where=exp12 > exp26, color="#93c47d", alpha=0.6, interpolate=True)
    fb_12dn = dict(y1=exp12.values, y2=exp26.values, where=exp12 < exp26, color="#e06666", alpha=0.6, interpolate=True)
    fb_exp12 = [fb_12up, fb_12dn]

    fb_macd_up = dict(y1=macd.values, y2=signal.values, where=signal < macd, color="#93c47d", alpha=0.6,
                      interpolate=True)
    fb_macd_dn = dict(y1=macd.values, y2=signal.values, where=signal > macd, color="#e06666", alpha=0.6,
                      interpolate=True)
    fb_macd_up['panel'] = 1
    fb_macd_dn['panel'] = 1

    fb_macd = [fb_macd_up, fb_macd_dn]

    apds = [mpf.make_addplot(exp12, color='lime'),
            mpf.make_addplot(exp26, color='c'),
            mpf.make_addplot(histogram, type='bar', width=0.7, panel=1,
                             color='dimgray', alpha=0.65, secondary_y=True),
            mpf.make_addplot(macd, panel=1, color='fuchsia', secondary_y=False),
            mpf.make_addplot(signal, panel=1, color='b', secondary_y=False)  # ,fill_between=fb_macd),
            ]

    s = mpf.make_mpf_style(base_mpf_style='blueskies', facecolor='aliceblue', rc={'figure.facecolor':'lightcyan'})
    last_close = df['close'].iloc[-1]

    save = dict(fname='tsave300.png', dpi=300, pad_inches=0.25)
    save2 = dict(fname='tsave3002.png', dpi=300, pad_inches=0.25)
    mpf.plot(df, type='candle', addplot=apds, figscale=1.6, figratio=(1, 1), title='\n\nMACD',
             style=s, volume=True, volume_panel=2, panel_ratios=(3, 6, 1), tight_layout=True,
             fill_between=fb_macd + fb_exp12, savefig=save)
    s = mpf.make_mpf_style(base_mpf_style='mike', rc={'figure.facecolor': 'lightgray'})

    mpf.plot(df, type='candle', addplot=apds, figscale=1.1, figratio=(1, 1), title=event['name'], tight_layout=True,
             style=s, volume=True, volume_panel=2, panel_ratios=(4, 3, 1), savefig=save2)
    mpf.show()


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
