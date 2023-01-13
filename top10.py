import tushare as ts
import pandas as pd
import tkinter
from tkinter import ttk
import datetime
import numpy as np
np.warnings.filterwarnings('ignore')

if __name__ != '__main__':
    global pro, res1, res2, res3

    t = datetime.date.today().strftime('%Y%m%d')
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    str_yes = datetime.datetime.strftime(yesterday, '%Y%m%d')

    ts.set_token('7184049e88a0d416150a596c4d97f46a854c24d4114030f23424b6d1')
    pro = ts.pro_api()
    df = pro.query('daily_basic', ts_code='', trade_date=str_yes, fields='ts_code,trade_date,total_mv,ps,pe,pb')
    # initial variable ：PE PB MarketValue
    PE_T = 10
    PB_T = 5
    MV = 5.0e+05
    # we choose the a range of  PE<=10,PB<=5,MV<=5e05
    df_choose = df[(df.pe <= PE_T) & (df.pb <= PB_T) & (df.total_mv <= MV)]
    # sort stocks by total market value in reverse order
    df_choose = df_choose.sort_values(by='total_mv', ascending=False)
    # select top 10 market value stocks
    df_choose = df_choose.reset_index(drop=True).loc[:9]
    res1 = df_choose[['ts_code', 'pe', 'pb', 'total_mv']]



    trendence = pro.top_list(trade_date=str_yes)
    # calculate net buy amount by buy-sell
    trendence["Net purchase"] = trendence[["l_buy", "l_sell"]].apply(lambda x: x["l_buy"] - x["l_sell"], axis=1)
    # calculate total amount buy amount by buy+sell
    trendence["Total transaction amount"] = trendence[["l_buy", "l_sell"]].apply(lambda x: x["l_buy"] + x["l_sell"],
                                                                                 axis=1)
    # remain five attributes in dataframe
    res3 = trendence[['ts_code', 'name', 'Net purchase', 'Total transaction amount', 'pct_change']]
    # sort stocks by net purchase value in reverse order
    res3 = res3.sort_values(by='Net purchase', ascending=False)
    # Remove duplicate
    res3 = res3.drop_duplicates(subset=['ts_code'], keep='first')
    # select top 10 net amount stocks
    res3 = res3.reset_index(drop=True).loc[:9]

    # We are based on the Fama-French three-factor model theory:
    # divide the PB of stocks into large and smal,
    # and divide the market value of stocks into large, medium, and small.
    # The factor of scale and value is obtained through market value weighting
    # (the size factor is the equal weighted average of three small market value
    # combinations minus the equal weighted average of three large market value combinations).
    # Finally, the stocks whose predicted value is lower than the current value are obtained through Alpha intercept.
    # These stocks are stocks that may rise in the future.

    # Calculate the market value-weighted rate of return function,
    # MV is the group corresponding to the market value classification,
    # and book_value is the group corresponding to the classification of the account-to-market value ratio
    def weighted(stocks, MV, book_value):
        select = stocks[(stocks['NEGOTIABLEMV'] == MV) & (stocks['book_value'] == book_value)]
        market_value = select['mv'].values
        market_valuetotal = np.sum(market_value)  # Market value sum
        market_valueweighted = [mv / market_valuetotal for mv in market_value]  # Market value weighted weight
        stock_return = select['return'].values
        return_total = []  # the sum of the market value weighted rate of return
        for i in range(len(market_valueweighted)):
            return_total.append(market_valueweighted[i] * stock_return[i])
        return_total = np.sum(return_total)
        return return_total


    fin = pro.query('daily_basic', ts_code='', trade_date=str_yes,
                    fields='ts_code,trade_date,total_mv,ps,pe,pb,close')
    fin['pb'] = (fin['pb'] ** -1)
    # Calculate the 50% quantile of the market value for later classification
    size_gate = fin['total_mv'].quantile(0.50)
    # Calculate the 30% and 70% quantiles of the book-to-market value ratio for subsequent classification
    book_value_gate = [fin['total_mv'].quantile(0.30), fin['total_mv'].quantile(0.70)]
    fin.index = fin.ts_code
    # Sort by book value
    book_value_big = 3.0
    book_value_middle = 2.0
    book_value_small = 1.0
    # Sort by market value
    market_value_big = 2.0
    market_value_small = 1.0

    x_return = []
    daily = pro.daily(ts_code='', trade_date=str_yes)
    for stock in fin['ts_code']:
        stock_close1 = daily[daily['ts_code'] == stock]['pre_close'].values
        stock_close2 = daily[daily['ts_code'] == stock]['close'].values
        list_return = stock_close2 / stock_close1 - 1
        for x in list_return:
            stock_return = x
        pb = fin['pb'][stock]
        market_value = fin['total_mv'][stock]
        # Determine which category it belongs to
        if pb < book_value_gate[0]:
            if market_value < size_gate:
                label = [stock, stock_return, book_value_small, market_value_small, market_value]
            else:
                label = [stock, stock_return, book_value_small, market_value_big, market_value]
        elif pb < book_value_gate[1]:
            if market_value < size_gate:
                label = [stock, stock_return, book_value_middle, market_value_small, market_value]
            else:
                label = [stock, stock_return, book_value_middle, market_value_big, market_value]
        elif market_value < size_gate:
            label = [stock, stock_return, book_value_big, market_value_small, market_value]
        else:
            label = [stock, stock_return, book_value_big, market_value_big, market_value]
        if len(x_return) == 0:
            x_return = label
        else:
            x_return = np.vstack([x_return, label])

    stocks = pd.DataFrame(data=x_return, columns=['symbol', 'return', 'book_value', 'NEGOTIABLEMV', 'mv'])
    stocks.index = stocks.symbol
    columns = ['return', 'book_value', 'NEGOTIABLEMV', 'mv']

    for column in columns:
        stocks[column] = stocks[column].astype(np.float64)

    # Calculate scale factor and value factor and market rate of return
    # We use market capitalization weighted method
    # big MV weighted return of scale
    scale_factor_s = (weighted(stocks, market_value_small, book_value_small) + weighted(stocks, market_value_small,
                                                                                        book_value_middle) + weighted(
        stocks, market_value_small, book_value_big)) / 3
    # small MV weighted return of scale
    scale_factor_b = (weighted(stocks, market_value_big, book_value_small) + weighted(stocks, market_value_big,
                                                                                      book_value_middle) + weighted(
        stocks, market_value_big, book_value_big)) / 3
    # according theory Equal weighted average of small MV - equal weighted average of big MV
    scale_factor = scale_factor_s - scale_factor_b
    # big MV weighted return of value
    value_factor_b = (weighted(stocks, market_value_small, 3) + weighted(stocks, market_value_big, book_value_big)) / 2
    # small MV weighted return of value
    value_factor_s = (weighted(stocks, market_value_small, book_value_small) + weighted(stocks, market_value_big,
                                                                                        book_value_small)) / 2
    # according theory Equal weighted average of small MV - equal weighted average of big MV
    value_factor = value_factor_b - value_factor_s

    # Here is the average return level of stocks, 000300.SH represents the average level of the index
    close1 = daily[daily['ts_code'] == '000300.SH']['pre_close'].values
    close2 = daily[daily['ts_code'] == '000300.SH']['close'].values
    listt = close2 / close1 - 1
    market_return = 0
    for x in listt:
        market_return = x
    coff_pool = []

    for stock in stocks.index:
        x_value = np.array([[market_return], [scale_factor], [value_factor], [1.0]])
        y_value = np.array([stocks['return'][stock]])
        # OLS estimation coefficient
        coff = np.linalg.lstsq(x_value.T, y_value)[0][3]
        coff_pool.append(coff)
        # Top 10 Alpha stocks
    stocks['alpha'] = coff_pool
    res2 = stocks[stocks.alpha < 0].sort_values(by='alpha').head(10)
    res2 = res2[['symbol','return','mv','alpha']]
    # sort stocks by total market value in reverse order
    res2 = stocks.sort_values(by='alpha', ascending=False)
    # select top 10 market value stocks
    res2= res2.reset_index(drop=True).loc[:9]


def top10PEPB(frame):
    w = tkinter.Label(frame, text="Yesterday Top 10 P/E Ratio P/B Ratio Stock Selection Strategy：", font=("微软雅黑", 15))
    w.grid(row=0, column=0)  # grid相当于pack

    columns = ("ts_code", "pe", "pb", "total_mv")  # #定义列
    ybar = ttk.Scrollbar(frame, orient='vertical')  # 滚动条

    tree = ttk.Treeview(frame, columns=columns, yscrollcommand=ybar.set, height=20)  # #创建表格对象
    for col in range(len(columns)):
        tree.column(columns[col], width=250)

    ybar['command'] = tree.yview

    for col in columns:  # 添加标题
        tree.heading(col, text=col)

    for index, row in res1.iterrows():
        tree.insert("", index, text=index + 1, values=(row['ts_code'], row['pe'], row['pb'], row['total_mv']))

    # tree.tag_configure("ttk",background='yellow')

    ttk.Style().theme_use('clam')
    ttk.Style().configure("Treeview", background="black", foreground="#FFFF33", rowheight=30, font=("微软雅黑", 15))
    ttk.Style().configure("Treeview.Heading", background="#FFFF99", foreground="Black", font=("微软雅黑", 15), rowheight=30)
    # tree.tag_configure('oddrow', background='orange')
    # tree.tag_configure('evenrow', background='purple')
    tree.grid(row=1, column=0)  # grid方案
    ybar.grid(row=1, column=1, sticky='ns')


def top10South(frame):
    w = tkinter.Label(frame, text="Yesterday Top 10 Alpha Stocks(Fama-French Three Factors Model) Trading:", font=("微软雅黑", 15))
    w.grid(row=0, column=0)  # grid相当于pack

    columns = ('symbol','return','mv','alpha')  # #定义列
    ybar = ttk.Scrollbar(frame, orient='vertical')  # 滚动条
    # xbar = ttk.Scrollbar(frame, orient=tkinter.HORIZONTAL)

    tree = ttk.Treeview(frame, columns=columns, yscrollcommand=ybar.set, height=20)  # #创建表格对象
    for col in range(len(columns)):  # 设置列
        tree.column(columns[col], width=200)
    ybar['command'] = tree.yview
    # xbar['command'] = tree.xview

    for col in columns:  # 添加标题
        tree.heading(col, text=col)

    for index, row in res2.iterrows():
        tree.insert("", index, text=index + 1, values=( row['symbol'], format(row['return'], '.10f'), row['mv'], format(row['alpha'], '.10f')))

    # tree.tag_configure("ttk",foreground="black")
    ttk.Style().theme_use('clam')
    ttk.Style().configure("Treeview", background="black", foreground="#FFFF33", rowheight=30, font=("微软雅黑", 15))
    ttk.Style().configure("Treeview.Heading", background="#FFFF99", foreground="Black", font=("微软雅黑", 15), rowheight=30)
    tree.grid(row=1, column=0)  # grid方案
    ybar.grid(row=1, column=1, sticky='ns')
    # xbar.grid(row=2, column=0, sticky='ew')


def top10Trans(frame):
    w = tkinter.Label(frame, text="Yesterday TOP 10 Stocks with The Largest Transaction Amount:", font=("微软雅黑", 15))
    w.grid(row=0, column=0)  # grid相当于pack

    columns = ("ts_code", "name", "Net purchase", "Total transaction amount", "pct_change")  # #定义列
    ybar = ttk.Scrollbar(frame, orient='vertical')  # 滚动条

    tree = ttk.Treeview(frame, columns=columns, yscrollcommand=ybar.set, height=20)  # #创建表格对象
    for col in range(len(columns)):  # 设置列
        tree.column(columns[col], width=250)

    ybar['command'] = tree.yview

    for col in columns:  # 添加标题
        tree.heading(col, text=col)

    for index, row in res3.iterrows():
        tree.insert("", index, text=index + 1, values=(
        row['ts_code'], row['name'], row['Net purchase'], row['Total transaction amount'], row['pct_change']))

    # tree.tag_configure("ttk",foreground="black")
    ttk.Style().theme_use('clam')
    ttk.Style().configure("Treeview", background="black", foreground="#FFFF33", rowheight=30, font=("微软雅黑", 15))
    ttk.Style().configure("Treeview.Heading", background="#FFFF99", foreground="Black", font=("微软雅黑", 15), rowheight=30)
    tree.grid(row=1, column=0)  # grid方案
    ybar.grid(row=1, column=1, sticky='ns')
