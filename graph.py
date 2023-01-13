import tushare as ts
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import mplfinance as mpf
import matplotlib as mpl  # 用于设置曲线参数
from cycler import cycler  # 用于定制线条颜色


def data_graph(year, month, data_name):
    data_fetch = pro.moneyflow_hsgt(start_date=year + month + '01', end_date=year + month + '31')  # one year
    date = []
    for item in data_fetch['trade_date']:
        date.append(item[6:8])  # date
    data_fetch['positive'] = data_fetch[data_name] > 0  # filter
    f = plt.figure(figsize=(18, 7), dpi=80)
    plt.subplot(121)  # two subplots
    plt.grid(axis='y', zorder=1)
    plt.bar(date[::-1], data_fetch[data_name][::-1], color=data_fetch['positive'][::-1].map({True: 'r', False: 'g'}),
            zorder=2)
    plt.xlabel('date')
    plt.ylabel('amount(million yuan)')
    plt.subplot(122)
    plt.axhline(y=0, c='y', zorder=1)  # y = 0 line
    plt.plot(date[::-1], data_fetch[data_name][::-1], color='b', marker='o', zorder=2)
    plt.grid(axis='y')
    plt.suptitle('Results of ' + data_name + ' in ' + year + '.' + month, fontsize=23, fontweight='bold')
    plt.xlabel('date')
    plt.ylabel('amount(million yuan)')
    plt.close()
    return f


def ns_compare(year, month):
    data_fetch = pro.moneyflow_hsgt(start_date=year + month + '01', end_date=year + month + '31')
    date = []
    for item in data_fetch['trade_date']:
        date.append(item[6:8])
    fig = plt.figure(figsize=(18, 7), dpi=80)
    plt.axhline(y=0, c='y', zorder=1)
    #  two different colored lines
    plt.plot(date[::-1], data_fetch['north_money'][::-1], label='north_money', zorder=2)
    plt.plot(date[::-1], data_fetch['south_money'][::-1], label='south_money', zorder=3)
    plt.xlabel('date')
    plt.ylabel('amount(million yuan)')
    plt.title('Comparison of North_money and South_money in ' + year + '.' + month, fontsize=23, fontweight='bold')
    plt.legend(loc='best', fontsize=16, frameon=True)
    plt.grid(axis='y')
    plt.close()
    return fig


def K_chart(stock_code):
    # 导入股票数据
    today = datetime.date.today()
    str_today = datetime.datetime.strftime(today, '%Y%m%d')
    last_year = today - datetime.timedelta(days=365)
    str_yesteryear = datetime.datetime.strftime(last_year, '%Y%m%d')  # 去年今日
    pro = ts.pro_api()
    df = pro.query('daily', ts_code=stock_code, start_date=str_yesteryear, end_date=str_today)  # 数据获取
    # 格式化列名，用于之后的绘制
    df.rename(
        columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume'},
        inplace=True)
    # 转换为日期格式
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    # 将日期列作为行索引
    df.set_index(['trade_date'], inplace=True)

    df = df[::-1]

    # 设置基本参数
    kwargs = dict(
        type='candle',  # 绘制图形的类型是K线图
        mav=(1, 5, 10),  # 均线类型,此处设置1,5,10日线
        volume=True,  # 显示成交量
        title='\nStock %s Candle_line (within one year)' % stock_code, ylabel='price',
        ylabel_lower='Shares\nTraded Volume',  # 设置成交量图一栏的标题
        figratio=(5, 1),  # 设置图形纵横比
        figscale=1.2)  # 设置图形尺寸
    # 设置K线线柱颜色
    mc = mpf.make_marketcolors(
        up='red',  # 收盘价大于等于开盘价
        down='green',  # 收盘价小于开盘价
        edge='i',  # K线线柱边缘颜色
        wick='i',  # 灯芯(上下影线)颜色
        volume='in',  # 成交量直方图的颜色
        inherit=True)

    # 设置图形风格
    s = mpf.make_mpf_style(
        y_on_right=False,
        marketcolors=mc)
    # 设置均线颜色
    mpl.rcParams['axes.prop_cycle'] = cycler(
        color=['dodgerblue', 'deeppink',
               'navy', 'teal', 'maroon', 'darkorange',
               'indigo'])

    # 设置线宽
    mpl.rcParams['lines.linewidth'] = .5

    # 图形绘制
    fig, ax = mpf.plot(df,
                       **kwargs,
                       style=s,
                       show_nontrading=False,
                       returnfig=True)

    return fig


if __name__ != '__main__':
    global pro

    ts.set_token('d5b6d75f290258a8ef23a7c3d1f020703cb893dc248733a6aead6d6a')
    pro = ts.pro_api()
