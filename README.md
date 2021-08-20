# gdrive-scroll
A tool for fetching and scrolling images (and music) stored in Google Drive.

This program was developed to be used on a Raspberry Pi for a digital signage purpose, but it should work fine on other *nix hosts.

### Dependencies
 - Python 3.7+
 - [feh](https://feh.finalrewind.org/) (requires [X](https://www.x.org/wiki/))
 - [mpg123](https://www.mpg123.de/)
 - [google-auth-oauthlib](https://google-auth-oauthlib.readthedocs.io/en/latest/index.html)

### Google Drive API
You will need to have a project in Google Cloud with a configured OAuth client in order to access the Drive API. The only scope needed in the consent screen is: `https://www.googleapis.com/auth/drive.readonly` Read more here: https://developers.google.com/drive/api/v3/about-sdk

### Credential Store
Before the first run of the program, create a JSON file with the following OAuth keys and values from your Google Cloud project:
````json
{"client_id": "FOO", "client_secret": "BAR"}
````
After the first run, the program will store the access token in that file and transparently take care of refreshing the token.

### Music
Since we use `mpg123` to play music, only MPEG (mp1/mp2/mp3) files are allowed.

### Usage
````
usage: scroll.py [-h] --credential-store CREDENTIAL_STORE --images-parent-id IMAGES_PARENT_ID [--music-parent-id MUSIC_PARENT_ID] [--slideshow-interval SLIDESHOW_INTERVAL]

A tool for fetching and scrolling images (and music) stored in Google Drive.

optional arguments:
  -h, --help            show this help message and exit
  --credential-store CREDENTIAL_STORE
                        Location of persistent credential store.
  --images-parent-id IMAGES_PARENT_ID
                        Google Drive parent (folder) id that contains the child images.
  --music-parent-id MUSIC_PARENT_ID
                        Google Drive parent (folder) id that contains the child music files.
  --slideshow-interval SLIDESHOW_INTERVAL
                        Number of seconds between images. (default: 10)

````
