from pydrive.auth import GoogleAuth

gauth = GoogleAuth("settings.yml")
auth_url = gauth.GetAuthUrl()
code = input(f"   GO TO   {auth-auth_url} and input code: ")
gauth.Auth(code)
gauth.SaveCredentialsFile()