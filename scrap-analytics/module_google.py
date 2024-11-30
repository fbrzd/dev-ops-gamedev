from os import system,listdir
import pandas as pd
from sys import argv
from pathlib import Path

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
    
    system(f"gsutil cp {URL_I} {PATH_LOCAL / 'data/google/install'}")
    system(f"gsutil cp {URL_T} {PATH_LOCAL / 'data/google/traffic'}")


# load all yearmonth & return merged dataframe
def merge_custom_summary():
    # path
    install_pwd = PATH_LOCAL / 'data/google/install' # "/home/fabrizoide/desk/hdd/unity/chibits/scraping/data/google/install/"
    traffic_pwd = PATH_LOCAL / 'data/google/traffic' # "/home/fabrizoide/desk/hdd/unity/chibits/scraping/data/google/traffic/"

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
    dt_summary.to_csv(PATH_LOCAL / 'data/google/last_summary.csv', index=False)
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

def sum_over_days(row, groupDays):
    global summary # need global because lambda
    #week = row["Date"].week
    group = (row['Date'] - DAY_ONE).days//groupDays
    if group not in summary:
        summary[group] = [
            0, # views
            0, # downloads
            
            0, # users
            0, # updates
            0 # uninstalls
        ]
    summary[group][0] += row["Store listing visitors"]
    summary[group][1] += row["Install events"]
    summary[group][2] += row["Active Device Installs"]
    summary[group][3] += row["Update events"]
    summary[group][4] += row["Uninstall events"]

def get_summary(groupDays=7):
    # prepare data
    df = merge_custom_summary()
    # sum by week
    df.apply(lambda row: sum_over_days(row, groupDays), axis=1)
    df = pd.DataFrame.from_dict(summary, orient='index', columns=['views','downloads','users','updates','uninstalls'])
    df['users'] //= groupDays
    return df

def setconfig(id_dev, app):
    global ID_DEV
    global APP
    ID_DEV = id_dev
    APP = app

def get_lastweek_report():
    file_path = PATH_LOCAL / 'data/google/last_summary.csv'  # Cambia esto por la ruta de tu archivo CSV
    data = pd.read_csv(file_path)

    # Asegurarnos de que la columna "date" sea de tipo datetime
    data['Date'] = pd.to_datetime(data['Date'])

    # Seleccionar las últimas 7 filas
    last_7_days = data.iloc[-8:-1]

    # Seleccionar las penúltimas 7 filas
    penultimate_7_days = data.iloc[-15:-8]

    # Agrupar las métricas para las últimas 7 filas
    last_week_summary = last_7_days[['Store listing visitors', 'Install events']].sum()
    last_week_range = f"{last_7_days['Date'].iloc[0].date()} - {last_7_days['Date'].iloc[-1].date()}"

    # Agrupar las métricas para las penúltimas 7 filas
    penultimate_week_summary = penultimate_7_days[['Store listing visitors', 'Install events']].sum()
    penultimate_week_range = f"{penultimate_7_days['Date'].iloc[0].date()} - {penultimate_7_days['Date'].iloc[-1].date()}"

    # Crear un DataFrame para mostrar ambas semanas
    comparison = pd.DataFrame({
        'date_range': [penultimate_week_range, last_week_range],
        'views': [penultimate_week_summary['Store listing visitors'], last_week_summary['Store listing visitors']],
        'downloads': [penultimate_week_summary['Install events'], last_week_summary['Install events']]
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
    title = "PLAY STORE"

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

ID_DEV = ""
APP = ""

summary = dict()
PATH_LOCAL = Path(__file__).parent