import pandas as pd
from datetime import datetime, date, timedelta
from sys import argv
import matplotlib.pyplot as plt
import json
from pathlib import Path

# stores
import module_google
import module_itchio

def format_week_metric(row_week, last_week=None, columns=['views', 'downloads']):
    values_str = list()
    for c in columns:
        if row_week[c] > last_week[c]:
            color = "\033[31m" if c == "uninstalls" else "\033[32m"
            values_str.append(f"{color}{row_week[c]}\033[0m")
        elif row_week[c] < last_week[c]:
            color = "\033[32m" if c == "uninstalls" else "\033[31m"
            values_str.append(f"{color}{row_week[c]}\033[0m")
        else: values_str.append(str(row_week[c]))
    
    return '\t\t'.join(values_str)

# OUPUT OPTION 1
def join_metrics_stores2(list_summaries, stores):
    min_week = min([s[0]['week'] for s in stores])
    main_summary = dict()
    for summary in list_summaries:
        for row in summary:
            if f"#{row['week']-min_week}" not in main_summary: main_summary['week'] = f"#{row['week']-min_week}"
            
    
    values_str = list()
    for i in range(5): # users, views, install, update, uninstall
        if curr_week[i] > last_week[i]:
            color = "\033[31m" if i == 4 else "\033[32m"
            values_str.append(f"{color}{curr_week[i]}\033[0m")
        elif curr_week[i] < last_week[i]:
            color = "\033[32m" if i == 4 else "\033[31m"
            values_str.append(f"{color}{curr_week[i]}\033[0m")
        else: values_str.append(str(curr_week[i]))
    
    return '\t'.join(values_str)


def calculate_header(list_summaries, stores):
    all_posible = ['views','downloads','uninstalls','updates','users', 'plays']
    final_columns = ['week']
    for col in all_posible:
        stores_parentesis = []
        for i,s in enumerate(list_summaries):
            if col in s.columns: stores_parentesis.append(stores[i])
        if len(stores_parentesis) > 0: final_columns.append(f"{col} ({','.join(stores_parentesis)})")
    final_columns.append("notes")
    return final_columns
def calculate_footer(df_main):
    last_row = list()
    for c in df_main:
        last_row.append(str(sum(df_main[c])))
    return last_row

def join_metrics_stores(list_summaries, stores):
    # header
    hd = calculate_header(list_summaries, stores)
    print("\033[1m" + '\t'.join(hd) + "\033[0m") # TODO: bold
    
    # merge
    df_main = pd.concat(list_summaries, axis=1)
    if len(list_summaries) > 1:
        df_main["views"] = df_main.pop("views").sum(axis=1)
        df_main["downloads"] = df_main.pop("downloads").sum(axis=1)
    df_main = df_main.fillna(0).astype(int)
    df_main = df_main[filter(lambda x: x in df_main.columns, ('views','downloads','uninstalls','updates','users', 'plays'))]

    # show data
    min_week = min(df_main.index)
    data_dict = dict()
    for index, row in df_main.iterrows():
        try:
            date1 = DAY_ONE + timedelta(days=DAYS_GROUP*index) 
            date2 = DAY_ONE + timedelta(days=DAYS_GROUP*(index+1))
            row = format_week_metric(row, df_main.loc[index-1] if index > min_week else row, df_main.columns)
            print(f"# {index - min_week + 1}\t{row}\t\t{search_milestones2(date1, date2)}")
        except:
            print(f"# {index - min_week +1} row error")
    
    print("\033[1m" + 'total\t'+'\t\t'.join(calculate_footer(df_main)) + "\033[0m") # TODO: bold
    
# milestones
def search_milestones2(dt1, dt2):
    list_notes = list()
    for t,n in milestones:
        if dt1 <= t < dt2: list_notes.append(n)
    return ', '.join(list_notes)

def graphics(list_summaries, stores, col='downloads'):
    # stores
    s_names = {'g':'google', 'i':'itchio', 's':'steam', 'h':'huawei'}
    mx = 0
    for i,store in enumerate(list_summaries):
        if len(store) > mx: mx = len(store)
        plt.plot(range(1, mx+1), store[col], label=s_names[stores[i]])
    
    # milestones
    df_main = pd.concat(list_summaries, axis=1)
    min_week = min(df_main.index)
    for i in range(min_week, min_week + mx):
        if search_milestones(i):
            plt.scatter(i-min_week+1, 0, marker='o', c='g')
            #plt.text(i, 100,s=m+' : '+l)
    plt.title(col)
    plt.legend()
    plt.show()

def read_config():
    with open(PATH_LOCAL / "config.json") as f:
        data = json.load(f)
    return data

# init
flagGoogle = '-g' in argv
flagItchio = '-i' in argv
stores_used = list()
PATH_LOCAL = Path(__file__).parent
DAYS_GROUP = int(argv[argv.index('-group')+1]) if '-group' in argv else 7

# config
config = read_config()
milestones = list(map(lambda x: (datetime.strptime(x[0], "%Y-%m-%d"), x[1]), config["milestones"]))
DAY_ONE = datetime.strptime(config["dayone"], "%Y-%m-%d")
module_google.DAY_ONE = DAY_ONE
module_itchio.DAY_ONE = DAY_ONE

if flagGoogle: module_google.setconfig(config["google"]["id_dev"], config["google"]["app"])
if flagItchio: module_itchio.setconfig(config["itchio"]["username"], config["itchio"]["password"], config["itchio"]["id_game"])

# refresh some year-month metric
if '-download' in argv:
    if flagGoogle:
        module_google.download_yearmonth(argv[argv.index('-download') + 1])
    if flagItchio:
        module_itchio.download_yearmonth(argv[argv.index('-download') + 1])

list_summaries = list()
if flagGoogle:
    list_summaries.append(module_google.get_summary(DAYS_GROUP))
    stores_used.append('g')

if flagItchio:
    list_summaries.append(module_itchio.get_summary(DAYS_GROUP))
    stores_used.append('i')

# show
if '-noshow' not in argv: join_metrics_stores(list_summaries, stores_used)

if '-report' in argv:
    str_report = datetime.now().strftime("%Y-%m-%d") + '\n'
    if flagGoogle: str_report += f"\n{module_google.get_lastweek_report()}\n"
    if flagItchio: str_report += f"\n{module_itchio.get_lastweek_report()}\n"

    with open(PATH_LOCAL / "report.txt", 'w') as f: f.write(str_report)

if '-graph' in argv:
    graphics(list_summaries, stores_used, argv[argv.index('-graph') + 1])