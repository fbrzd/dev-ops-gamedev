# Metrics Game Downloader
Downloader csv with data about your game

## Config File
* Google Play Store:
  Need setup gsutil tool ([tutorial](https://cloud.google.com/storage/docs/gsutil_install#creds-gsutil)).
  - id_dev (form url at google play console)
  - app (com.< publisher >.< appname >)
* Itchio:
  No exists automatic way to get all historical data, just latest 30 days. Fill up your game's data until 30 days before now, then you need to run this program at least once every 30 days.
  - username (login user)
  - password (login password)
  - id_game (from url at "analytics" tab for your game)