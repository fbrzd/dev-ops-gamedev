from os import system,listdir,path
import pandas as pd
#from datetime import datetime,date
from sys import argv
import requests

# download & write one yearmonth
def download_yearmonth(date):
    global ID_DEV
    global APP
    
    BUCKET_I = "stats/installs/installs"
    BUCKET_T = "stats/store_performance/store_performance"
    FILE_I = "overview.csv"
    FILE_T = "traffic_source.csv"

    URL_I = f"gs://pubsite_prod_{ID_DEV}/{BUCKET_I}_{APP}_{date}_{FILE_I}"
    URL_T = f"gs://pubsite_prod_{ID_DEV}/{BUCKET_T}_{APP}_{date}_{FILE_T}"
    
    system(f"gsutil cp {URL_I} {PATH_LOCAL}/data/google/install")
    system(f"gsutil cp {URL_T} {PATH_LOCAL}/data/google/traffic")


# load all yearmonth & return merged dataframe
def merge_custom_summary():
    # path
    install_pwd = PATH_LOCAL+'/data/google/install' # "/home/fabrizoide/desk/hdd/unity/chibits/scraping/data/google/install/"
    traffic_pwd = PATH_LOCAL+'/data/google/traffic' # "/home/fabrizoide/desk/hdd/unity/chibits/scraping/data/google/traffic/"

    # load all yearmonth
    dt_i = list()
    for s in listdir(install_pwd):
        with open(f"{install_pwd}/{s}", encoding='utf-16') as f:
            dt_i.append(pd.read_csv(f, usecols=[0,8,9,10,11], parse_dates=[0])) # date, users, install, update, uninstall
    dt_t = list()
    for s in listdir(traffic_pwd):
        with open(f'{traffic_pwd}/{s}', encoding='utf-16') as f:
            dt_t.append(pd.read_csv(f, usecols=[0,7], parse_dates=[0])) # date, views

    # merge
    dt_i = pd.concat(dt_i)
    dt_t = pd.concat(dt_t)
    dt_summary = pd.merge(dt_i, dt_t, on="Date", how="outer")
    dt_summary.loc[:, dt_summary.columns != 'Date'] = dt_summary.loc[:, dt_summary.columns != 'Date'].fillna(0).astype(int)
    dt_summary.sort_values(by="Date", inplace=True)
    dt_summary.to_csv(PATH_LOCAL+'/data/google/last_summary.csv', index=False)
    return dt_summary

# create summary
def sum_over_week(row):
    global summary # need global because lambda
    #week = row["Date"].week
    week = (row['Date'] - DAY_ONE).days//7
    if week not in summary:
        summary[week] = [
            0, # views
            0, # downloads
            
            0, # users
            0, # updates
            0 # uninstalls
        ]
    summary[week][0] += row["Store listing visitors"]
    summary[week][1] += row["Install events"]
    summary[week][2] += row["Active Device Installs"]
    summary[week][3] += row["Update events"]
    summary[week][4] += row["Uninstall events"]


def get_summary():
    # prepare data
    df = merge_custom_summary()
    # sum by week
    df.apply(lambda row: sum_over_week(row), axis=1)
    df = pd.DataFrame.from_dict(summary, orient='index', columns=['views','downloads','users','updates','uninstalls'])
    df['users'] //= 7
    return df

def setconfig(id_dev, app):
    global ID_DEV
    global APP
    ID_DEV = id_dev
    APP = app

ID_DEV = ""
APP = ""

summary = dict()
PATH_LOCAL = path.dirname(__file__)