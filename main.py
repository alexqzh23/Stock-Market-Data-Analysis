from pandas.core.frame import DataFrame
import tushare as ts
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import *
import tkinter
from tkinter import Frame, ttk
import graph
import datetime
import re
import top10


# Response to quit message
def quit():
    win.quit()
    win.destroy()


# Response to menu message
def on_change(fnc):
    def executor():
        global frame

        # Common code that destroy the frame that contents are showing on
        frame.destroy()
        frame = Frame(container)
        frame.pack()

        # Call the actual handler
        fnc()

    return executor


# Showing the chart
def show_chart(fig):
    # Frame that is used to show the chart
    if hasattr(show_chart, 'frm') and show_chart.frm != None:
        show_chart.frm.destroy()

    show_chart.frm = Frame(frame)
    show_chart.frm.pack(side=TOP)

    # Draw the figure to the frame throught canvas
    canvas = FigureCanvasTkAgg(fig, master=show_chart.frm)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    # Show the toolbar of matplotlib
    toolbar = NavigationToolbar2Tk(canvas, show_chart.frm)
    toolbar.update()
    canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)


# Showing chart 1
def check_chart1(year, month, data_name):
    def show():
        fig = graph.data_graph(year.get(), month.get(), data_name.get())
        show_chart(fig)

    return show


# Showing chart 2
def check_chart2(year, month):
    def show():
        fig = graph.ns_compare(year.get(), month.get())
        show_chart(fig)

    return show


# Show data in graph
def show_graph():
    global frame

    frm1 = Frame(frame)
    frm1.pack(side=TOP)

    # Create and show the controls
    Label(frm1, text='Data name:').pack(side=LEFT)

    data_name = StringVar(value='ggt_ss')
    comboxlist = ttk.Combobox(frm1, textvariable=data_name, state='readonly')
    comboxlist["values"] = ('ggt_ss', 'ggt_sz', 'sgt', 'hgt')
    comboxlist.current(0)
    comboxlist.pack(side=LEFT)

    Label(frm1, text='Year').pack(side=LEFT)

    year = StringVar(value=str(datetime.date.today().year))
    comboxlist = ttk.Combobox(frm1, textvariable=year, state='readonly')
    comboxlist["values"] = tuple(range(datetime.date.today().year - 6, datetime.date.today().year + 1))
    comboxlist.current(6)
    comboxlist.pack(side=LEFT)

    Label(frm1, text='Month').pack(side=LEFT)

    month = StringVar(value='01')
    comboxlist = ttk.Combobox(frm1, textvariable=month, state='readonly')
    comboxlist["values"] = tuple(['0' + str(s) for s in range(1, 10)] + [10, 11, 12])
    comboxlist.current(0)
    comboxlist.pack(side=LEFT)

    Button(frm1, text='Show Chart1', command=check_chart1(year, month, data_name)).pack(side=LEFT)

    frm2 = Frame(frame)
    frm2.pack(side=TOP)

    Label(frm2, text='Year').pack(side=LEFT)
    year = StringVar(value=str(datetime.date.today().year))
    comboxlist = ttk.Combobox(frm2, textvariable=year, state='readonly')
    comboxlist["values"] = tuple(range(datetime.date.today().year - 6, datetime.date.today().year + 1))
    comboxlist.current(6)
    comboxlist.pack(side=LEFT)

    Label(frm2, text='Month').pack(side=LEFT)

    month = StringVar(value='01')
    comboxlist = ttk.Combobox(frm2, textvariable=month, state='readonly')
    comboxlist["values"] = tuple(['0' + str(s) for s in range(1, 10)] + [10, 11, 12])
    comboxlist.current(0)
    comboxlist.pack(side=LEFT)

    Button(frm2, text='Show Chart2', command=check_chart2(year, month)).pack(side=LEFT)


# Show data in table
def show_table():
    global frame

    if not hasattr(show_table, 'i_data'):
        show_table.i_data = data
    if not hasattr(show_table, 'last_search'):
        show_table.last_search = ''

    # Create and show the controls
    frm0 = Frame(frame)
    frm0.pack(side=TOP)

    txt = StringVar(value=show_table.last_search)
    entry = Entry(frm0, textvariable=txt)
    entry.pack(side=LEFT)

    btn = Button(frm0, text='Search', command=on_search(txt))
    btn.pack(side=LEFT)

    frm1 = Frame(frame)
    frm1.pack(side=TOP)

    columns = ("ts_code", "symbol", "name", "area", "industry", "list_date", "market")
    ybar = ttk.Scrollbar(frm1, orient='vertical')

    tree = ttk.Treeview(frm1, columns=columns, yscrollcommand=ybar.set, height=20)
    ybar['command'] = tree.yview

    tree.column("ts_code", width=150)
    tree.column("symbol", width=150)
    tree.column("name", width=150)
    tree.column("area", width=150)
    tree.column("industry", width=150)
    tree.column("list_date", width=150)
    tree.column("market", width=150)

    for index, row in show_table.i_data.iterrows():
        tree.insert("", index, text=index, values=(
            row['ts_code'], row['symbol'], row['name'], row['area'], row['industry'], row['list_date'], row['market']))

    for col in columns:
        tree.heading(col, text=col + ' ▴▼', command=lambda _col=col: treeview_sort_column(tree, _col, True))
    tree.grid(row=0, column=0)
    ybar.grid(row=0, column=1, sticky='ns')

    tree.bind('<Double-Button-1>', tv_on_click(tree))
    tree.tag_configure("ttk", foreground="black")


# Response to user's search action
def on_search(txt):
    def handler():
        df = DataFrame()
        # Nothing to search, then show all data
        if txt.get() == '':
            # Pass the result through show_table()'s static variable,
            # since the call back function cannot pass arguments
            show_table.i_data = data
            show_table.last_search = ''
            # Apply changes to the table
            on_change(show_table)()
            return

        # Search all the rows
        for index, row in data.iterrows():
            # Construct pattern of regular expression
            pattern = '.*' + txt.get() + '.*'
            # Add matched row to result
            if re.match(pattern, row['name'], re.I):
                df = df.append(row)

            # Same as above
        show_table.i_data = df
        show_table.last_search = txt.get()
        on_change(show_table)()

    return handler


# Show the K chart at a seperate windows, since the chart is too big.
def show_K_chart(fig):
    # Handler of event of closing window
    # We need to destroy the window manually and
    # set wnd to None to show that the window is destroyed.
    def on_close():
        show_K_chart.wnd.destroy()
        show_K_chart.wnd = None

    # Use static variable to make sure there is only one window that
    # is showing the chart.
    if hasattr(show_K_chart, 'wnd') and show_K_chart.wnd != None:
        show_K_chart.wnd.destroy()

    # Create window
    show_K_chart.wnd = Tk()
    show_K_chart.wnd.title('K Chart')
    # Bind handler when user click close button
    show_K_chart.wnd.protocol('WM_DELETE_WINDOW', on_close)

    canvas = FigureCanvasTkAgg(fig, master=show_K_chart.wnd)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, show_K_chart.wnd)
    toolbar.update()
    canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)


# Response to user's click on the tree view
def tv_on_click(tv):
    def handler(event):
        item = tv.selection()
        if item:
            txt = tv.item(item[0], 'text')
            ts_code = data['ts_code'][int(txt)]
            fig = graph.K_chart(ts_code)
            show_K_chart(fig)

    return handler


# 当用户点击表头排序时，箭头会相应改变
def arrows(arg):
    if (arg):
        return " ▲▾"
    else:
        return " ▴▼"


# 这个是排序函数
def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]

    l.sort(reverse=reverse)  # 排序方式

    for index, (val, k) in enumerate(l):  # 根据排序后索引移动
        tv.move(k, '', index)
    tv.heading(col, text=col + arrows(reverse),
               command=lambda: treeview_sort_column(tv, col, not reverse))  # 重写标题，使之成为再点倒序的标题


# Following 3 functions are call back function that
# handles user's clicks on strategy menu
def show_strategy1():
    top10.top10South(frame)


def show_strategy2():
    top10.top10PEPB(frame)


def show_strategy3():
    top10.top10Trans(frame)


# Entry point of program
# Do the initialization
def main():
    global pro, container, frame, win, data

    ts.set_token('3d84491cf6fb4ed1f09d046703f143332a8b40294ccba5b31d55858d')
    pro = ts.pro_api()

    # 此部分为part1：股票基本信息，已经保存在字典data中，可以用字典的方式遍历或者查询
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date,market')

    # Create window
    win = tkinter.Tk()
    win.title('Stock Analysis')

    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    win.geometry("%dx%d" % (screen_w, screen_h))

    container = Frame(win)
    container.pack(side=TOP)

    frame = Frame(container)
    frame.pack()

    # Add menu
    menu_bar = Menu(win)
    menu = Menu(menu_bar, tearoff=0)

    menu.add_command(label="Table", command=on_change(show_table))
    menu.add_command(label='Graph', command=on_change(show_graph))
    menu.add_separator()
    menu.add_command(label="Exit", command=quit)
    menu_bar.add_cascade(label="Type", menu=menu)

    menu = Menu(menu_bar, tearoff=0)
    menu.add_command(label="Strategy 1", command=on_change(show_strategy1))
    menu.add_command(label="Strategy 2", command=on_change(show_strategy2))
    menu.add_command(label="Strategy 3", command=on_change(show_strategy3))

    menu_bar.add_cascade(label='Strategy', menu=menu)

    win.config(menu=menu_bar)

    ttk.Style().theme_use('default')
    ttk.Style().configure("Treeview", background="black", foreground="#FFFF33", rowheight=30, font=("微软雅黑", 15))
    ttk.Style().configure("Treeview.Heading", background="#FFFF99", foreground="Black", font=("微软雅黑", 15), rowheight=30)

    # Show the table by default
    show_table()

    win.mainloop()  # Show the window


# Define entry point of program
if __name__ == '__main__':
    main()
