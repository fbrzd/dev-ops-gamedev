import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from os import listdir
from pathlib import Path
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
        with open(PATH_LOCAL / 'data/itchio/last_summary.csv') as f: # PATH ISSUE
            df_local = pd.read_csv(f, parse_dates=[0])
            df_main = df_local.merge(df_cur, on=['Date',"Views","Downloads"], how='outer')
        df_main.to_csv(PATH_LOCAL / 'data/itchio/last_summary.csv', index=False)
        return df_main
        # -------------------- TEMPORAL
        
        # write
        #df_cur.to_csv(f"{date}.csv", index=False)

# load all yearmonth & return merged dataframe
def merge_custom_summary():
    # path
    data_pwd = PATH_LOCAL / 'data/itchio'
    
    # load all yearmonth
    dt_summary = list()
    for s in listdir(data_pwd):
        with open(f"{data_pwd}/{s}") as f:
            dt_summary.append(pd.read_csv(f, parse_dates=[0])) # views, downloads
    
    # merge
    dt_summary = pd.concat(dt_summary)
    dt_summary.sort_values(by="Date", inplace=True)
    dt_summary.to_csv(PATH_LOCAL / 'data/itchio/last_summary.csv', index=False)
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

def sum_over_days(row, groupDays):
    global summary # need global because lambda
    group = (row['Date'] - DAY_ONE).days//groupDays
    if group not in summary:
        summary[group] = [
            0, # views
            0 # downloads
        ]
    summary[group][0] += row["Views"]
    summary[group][1] += row["Downloads"]

def get_summary(groupDays=7):
    # prepare data
    df = merge_custom_summary()
    # sum by week
    df.apply(lambda row: sum_over_days(row, groupDays), axis=1)
    return pd.DataFrame.from_dict(summary, orient='index', columns=['views','downloads'])

def setconfig(username, password, id_game):
    global PAYLOAD
    global ID_GAME
    PAYLOAD = {"username": username, "password": password}
    ID_GAME = id_game

def get_lastweek_report():
    file_path = PATH_LOCAL / 'data/itchio/last_summary.csv'  # Cambia esto por la ruta de tu archivo CSV
    data = pd.read_csv(file_path)

    # Asegurarnos de que la columna "date" sea de tipo datetime
    data['Date'] = pd.to_datetime(data['Date'])

    # Seleccionar las últimas 7 filas
    last_7_days = data.iloc[-8:-1]

    # Seleccionar las penúltimas 7 filas
    penultimate_7_days = data.iloc[-15:-8]

    # Agrupar las métricas para las últimas 7 filas
    last_week_summary = last_7_days[['Views', 'Downloads']].sum()
    last_week_range = f"{last_7_days['Date'].iloc[0].date()} - {last_7_days['Date'].iloc[-1].date()}"

    # Agrupar las métricas para las penúltimas 7 filas
    penultimate_week_summary = penultimate_7_days[['Views', 'Downloads']].sum()
    penultimate_week_range = f"{penultimate_7_days['Date'].iloc[0].date()} - {penultimate_7_days['Date'].iloc[-1].date()}"

    # Crear un DataFrame para mostrar ambas semanas
    comparison = pd.DataFrame({
        'date_range': [penultimate_week_range, last_week_range],
        'views': [penultimate_week_summary['Views'], last_week_summary['Views']],
        'downloads': [penultimate_week_summary['Downloads'], last_week_summary['Downloads']]
    }, index=['Penultimate Week', 'Last Week'])

    # Calcular la diferencia porcentual
    views_diff_percent = ((comparison.loc['Last Week', 'views'] - comparison.loc['Penultimate Week', 'views']) /
                        comparison.loc['Penultimate Week', 'views']) * 100
    downloads_diff_percent = ((comparison.loc['Last Week', 'downloads'] - comparison.loc['Penultimate Week', 'downloads']) /
                            comparison.loc['Penultimate Week', 'downloads']) * 100

    # Agregar la fila de diferencias porcentuales
    comparison.loc['% Change'] = [
        '',  # Sin rango de fechas para esta fila
        f"{'+' if views_diff_percent > 0 else ''}{int(views_diff_percent)}%",
        f"{'+' if downloads_diff_percent > 0 else ''}{int(downloads_diff_percent)}%"
    ]

    # Título personalizado
    title = "ITCHIO"

    # Crear el contenido del archivo con el formato solicitado
    views_penultimate = comparison.loc['Penultimate Week', 'views']
    views_last = comparison.loc['Last Week', 'views']
    views_diff = comparison.loc['% Change', 'views']

    downloads_penultimate = comparison.loc['Penultimate Week', 'downloads']
    downloads_last = comparison.loc['Last Week', 'downloads']
    downloads_diff = comparison.loc['% Change', 'downloads']

    output = f"""{title}
- views: {views_penultimate}  > {views_last} ({views_diff})
- downloads: {downloads_penultimate}  > {downloads_last} ({downloads_diff})"""

    # Guardar el contenido en un archivo .txt
    #file_path = "comparison.txt"  # Cambia el nombre del archivo si es necesario
    #with open(file_path, "w") as file:
    #    file.write(output)

    #print(f"Archivo guardado en: {file_path}")


    #print(comparison)
    return output

summary = dict()
PATH_LOCAL = Path(__file__).parent

# config
PAYLOAD = {}
ID_GAME = ""

# debug
#setconfig("fbrzd", "mortalkombat1997", "922624")
#get_lastweek_report()