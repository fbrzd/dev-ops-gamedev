from os import path, system, listdir, walk, environ
from sys import argv
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build as gbuild
from zipfile import ZipFile, ZIP_DEFLATED
import json

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
    elif plataform == "android": path_build += ".apk"
    elif plataform == "google": path_build += ".aab"
    
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
    if plataform == "google": google_deploy(f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}.aab")
    elif plataform == "android": namefile = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}.apk"
    else: namefile = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}-{plataform}.zip"
    
    if plataform != "google":
        dict_tags = {
            "linux":"linux",
            "windows":"windows",
            "webgl": "html5",
            "android": "android"
        }
        cmd = f"butler push --userversion {version} {namefile} {CONFIG['itchio']['user']}/{CONFIG['itchio']['game']}:{dict_tags[plataform]}"
        system(cmd)

def google_deploy(filename):
    # parameters
    service = gbuild('androidpublisher', 'v3')
    PACKAGE = "com.FBRZD.Chibits"
    
    # crate edit
    edit = service.edits()
    r = edit.insert(packageName=PACKAGE).execute()
    id_edit = r["id"]
    print(r)
    
    # upload .aab
    r_aab = edit.bundles().upload(
        packageName=PACKAGE,
        editId=id_edit,
        ackBundleInstallationWarning=False,
        media_body=filename,
        media_mime_type="application/octet-stream").execute()
    
    # update track
    with open("track-template.json") as f:
        tmp = json.load(f)
    tmp["releases"][0]["versionCodes"].append(str(r_aab["versionCode"]))

    r_track = edit.tracks().update(
        packageName=PACKAGE,
        editId=id_edit,
        track="production",
        body=tmp).execute()
    
    # validate & commit
    r_val = edit.validate(packageName=PACKAGE, editId=id_edit).execute()
    r_com = edit.commit(packageName=PACKAGE, editId=id_edit).execute()

def deploy_test(version, plataform):
    ids_remotes = CONFIG['drive']['ids_remotes']

    # init drive api
    gauth = GoogleAuth("settings.yml")
    drive = GoogleDrive(gauth)
    
    # update file
    f = drive.CreateFile({'id': ids_remotes[plataform]})
    
    if plataform == "android": path_zip = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}.apk"
    elif plataform == "google": path_zip = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}.aab"
    else: path_zip = f"{CONFIG['path-build']}/{version}/{plataform}/{CONFIG['project']}-{plataform}.zip"
    
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
    #service = build('androidpublisher', 'v3')
    deploy_prod(VERSION, PLATAFORM)
    print(f"{PLATAFORM}-{VERSION} deploy-prod done")
