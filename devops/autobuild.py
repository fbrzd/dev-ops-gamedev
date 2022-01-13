from os import path, system, listdir, walk
from sys import argv
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from zipfile import ZipFile, ZIP_DEFLATED

def setconfig():
    with open("config.json") as f:
        CONFIG = json.load(f)
    return CONFIG

def build(version, plataform):
    path_unity = CONFIG["path-unity"]
    path_project = CONFIG["path-project"]
    path_log = f"{CONFIG['path-build']}/{version}/{plataform}/log"
    path_build = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}"

    if plataform == "linux": path_build += ".x86_64"
    elif plataform == "windows": path_build += ".exe"
    
    command_build = f"{path_unity} -projectPath {path_project} -quit -batchmode -nographics -logFile {path_log} -executeMethod Builder.Build {plataform} {path_build}"
    system(command_build)

    if plataform == "webgl": # move build to proper folder
        system(f"mv -f {path_build}/* {path_build[:-5]}")
        system(f"rm {path_build} -r")

def compress(version, plataform):
    path_version = f"{CONFIG['path-build']}/{version}/{plataform}"
    with ZipFile(f"{path_version}/{CONFIG['project']}-{plataform}.zip", 'w', ZIP_DEFLATED) as z:
        for root, dirs, files in walk(path_version):
            for f in files:
                if f[-3:] in ("log", "zip"): continue
                else: z.write(path.join(root, f), f"{root[len(path_version):]}/{f}")


def deploy_prod(version, plataform):
    namefile = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}-{plataform}.zip"
    dict_tags = {
        "linux":"linux",
        "windows":"windows",
        "webgl": "html5"
    }
    cmd = f"butler push --userversion {version} {namefile} {CONFIG['itchio']['user']}/{CONFIG['itchio']['game']}:{dict_tags[plataform]}"
    system(cmd)

def deploy_test(version, plataform):
    ids_remotes = CONFIG['drive']['ids_remotes']

    # init drive api
    gauth = GoogleAuth("settings.yml")
    drive = GoogleDrive(gauth)
    
    # update file
    f = drive.CreateFile({'id': ids_remotes[plataform]})
    path_zip = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}-{plataform}.zip"
    f.SetContentFile(path_zip)
    f.Upload()

CONFIG = setconfig()

NAME_PROJECT = CONFIG['project']
PLATAFORM = argv[-2]
VERSION = argv[-1]

if '-build' in argv:
    build(VERSION, PLATAFORM)
    print(f"{PLATAFORM}-{VERSION} build done")

if '-compress' in argv:
    compress(VERSION,PLATAFORM)
    print(f"{PLATAFORM}-{VERSION} compress done")

if '-deploy-test' in argv: # drive
    deploy_test(VERSION, PLATAFORM)
    print(f"{PLATAFORM}-{VERSION} deploy-test done")

if '-deploy-prod' in argv: # itchio
    deploy_prod(VERSION, PLATAFORM)
    print(f"{PLATAFORM}-{VERSION} deploy-prod done")
