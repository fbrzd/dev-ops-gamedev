import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from os import listdir,path
from requests_html import HTMLSession

def parse_json(text):
    i = text.find("R.GameEdit.Analytics") + 21
    j = text.find(")", i)
    return json.loads(text[i:j])

# download & write one yearmonth
def download_yearmonth(date):
    global PAYLOAD
    global ID_GAME

    with requests.Session() as s:
        # login
        p = s.get('https://itch.io/login')
        soup = BeautifulSoup(p.content, features="lxml")
        PAYLOAD['csrf_token'] = soup.find('meta', attrs={'name': 'csrf_token'})['value']
        r = s.post('https://itch.io/login', data=PAYLOAD)
        
        # get summary
        r = s.get('https://itch.io/game/summary/'+ID_GAME)
        raw_data = parse_json(str(r.content))
        data_v = {'views':{}, 'date':{}}
        data_d = {'downloads':{}, 'date':{}}
        
        # create df
        dt_v = pd.DataFrame(map(lambda x: (x['date'], x['count']), raw_data['views']), columns=['Date', 'Views'])
        dt_d = pd.DataFrame(map(lambda x: (x['date'], x['count']), raw_data['downloads']), columns=['Date','Downloads'])
        df_cur = pd.merge(dt_v, dt_d, on="Date", how="outer")
        df_cur.loc[:, df_cur.columns != 'Date'] = df_cur.loc[:, df_cur.columns != 'Date'].fillna(0).astype(int)
        df_cur["Date"] = pd.to_datetime(df_cur["Date"], format="%Y/%m/%d")
        df_cur.sort_values(by="Date", inplace=True)
        
        # -------------------- TEMPORAL
        with open(PATH_LOCAL+'/data/itchio/last_summary.csv') as f: # PATH ISSUE
            df_local = pd.read_csv(f, parse_dates=[0])
            df_main = df_local.merge(df_cur, on=['Date',"Views","Downloads"], how='outer')
        df_main.to_csv(PATH_LOCAL+'/data/itchio/last_summary.csv', index=False)
        return df_main
        # -------------------- TEMPORAL
        
        # write
        #df_cur.to_csv(f"{date}.csv", index=False)

# load all yearmonth & return merged dataframe
def merge_custom_summary():
    # path
    data_pwd = PATH_LOCAL+'/data/itchio'
    
    # load all yearmonth
    dt_summary = list()
    for s in listdir(data_pwd):
        with open(f"{data_pwd}/{s}") as f:
            dt_summary.append(pd.read_csv(f, parse_dates=[0])) # views, downloads
    
    # merge
    dt_summary = pd.concat(dt_summary)
    dt_summary.sort_values(by="Date", inplace=True)
    dt_summary.to_csv(PATH_LOCAL+'/data/itchio/last_summary.csv', index=False)
    return dt_summary

# create summary
def sum_over_week(row):
    global summary # need global because lambda
    week = (row['Date'] - DAY_ONE).days//7
    if week not in summary:
        summary[week] = [
            0, # views
            0 # downloads
        ]
    summary[week][0] += row["Views"]
    summary[week][1] += row["Downloads"]

def get_summary():
    # prepare data
    df = merge_custom_summary()
    # sum by week
    df.apply(lambda row: sum_over_week(row), axis=1)
    return pd.DataFrame.from_dict(summary, orient='index', columns=['views','downloads'])

def setconfig(username, password, id_game):
    global PAYLOAD
    global ID_GAME
    PAYLOAD = {"username": username, "password": password}
    ID_GAME = id_game

summary = dict()
PATH_LOCAL = path.dirname(__file__)

# config
PAYLOAD = {}
ID_GAME = ""