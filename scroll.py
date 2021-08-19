import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from google_auth_oauthlib import get_user_credentials
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials


def main():
    parser = argparse.ArgumentParser(description='A tool for fetching and scrolling images stored in Google Drive.')
    parser.add_argument('--credential-store', required=True, help='Location of persistent credential store.')
    parser.add_argument('--images-parent-id', required=True, help='Google Drive parent (folder) id that contains the child images.')
    parser.add_argument('--music-parent-id', help='Google Drive parent (folder) id that contains the child music files.')
    parser.add_argument('--slideshow-interval', default=10, help='Number of seconds between images. (default: 10)')
    args = parser.parse_args()

    # https://developers.google.com/drive/api/v3/about-auth
    # https://google-auth.readthedocs.io/en/latest/user-guide.html#user-credentials
    # Tool for checking access tokens: https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=[TOKEN]

    # pylint: disable=subprocess-run-check
    # We are sending everything to the background anyway so using check won't affect anything.

    credential_path = pathlib.Path(args.credential_store)
    if credential_path.is_file():
        with open(credential_path) as stream:
            credentials_file = json.load(stream)

        # When we create the Credentials object later using **kwargs, the object behaves odd when expiry is set at initialization so we delete it.
        if 'expiry' in credentials_file:
            del credentials_file['expiry']
    else:
        print('ERROR: Credential store provided is not a file')
        sys.exit(1)

    # Assume this is the first run and we need to go through the OAuth workflow.
    if 'token' not in credentials_file:
        try:
            # https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.html#google_auth_oauthlib.get_user_credentials
            credentials = get_user_credentials(['https://www.googleapis.com/auth/drive.readonly'], credentials_file['client_id'], credentials_file['client_secret'])
        except KeyError:
            print('ERROR: Missing required keys (client_id or client_secret) in credential store.')
            sys.exit(1)
    else:
        credentials = Credentials(**credentials_file)

    # This requests Session object will handle token refresh and checking: https://google-auth.readthedocs.io/en/latest/reference/google.auth.transport.requests.html#google.auth.transport.requests.AuthorizedSession
    session = AuthorizedSession(credentials)

    # API: https://developers.google.com/drive/api/v3/reference/files/list
    # Query structure: https://developers.google.com/drive/api/v3/search-files#query_string_examples
    image_list = session.get(f'https://www.googleapis.com/drive/v3/files?supportsAllDrives=true&includeItemsFromAllDrives=true&q=\'{args.images_parent_id}\' in parents and trashed = false')
    image_files = [file for file in image_list.json()['files'] if file['mimeType'].startswith('image')]  # Images only, please.

    # Example /files response:
    # {
    #   "kind": "drive#fileList",
    #   "incompleteSearch": false,
    #   "files": [ ... ]
    # }

    images_dir = pathlib.Path('/tmp/gdrive-scroll/images')
    # See if there are existing images; if so, remove the images directory and its content then create a new directory.
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True)

    for image in image_files:
        # https://developers.google.com/drive/api/v3/reference/files/get
        file = session.get(f'https://www.googleapis.com/drive/v3/files/{image["id"]}?alt=media')

        # Example /files/ID response:
        # {
        #   "kind": "drive#file",
        #   "id": "FOO",
        #   "name": "FOO.jpg",
        #   "mimeType": "image/jpeg"
        # }

        with open(pathlib.Path(images_dir, image['name']), 'wb') as stream:
            stream.write(file.content)

    subprocess.run(f'feh --slideshow-delay {args.slideshow_interval} {images_dir} &', shell=True)

    # Do almost everything again but for music this time.
    if args.music_parent_id:
        music_list = session.get(f'https://www.googleapis.com/drive/v3/files?supportsAllDrives=true&includeItemsFromAllDrives=true&q=\'{args.music_parent_id}\' in parents and trashed = false')
        music_files = [file for file in music_list.json()['files'] if file['mimeType'] == 'audio/mpeg']  # MPEG only, please.
        print(music_list.json())

        music_dir = pathlib.Path('/tmp/gdrive-scroll/music')
        if music_dir.exists():
            shutil.rmtree(music_dir)
        music_dir.mkdir(parents=True)

        for music in music_files:
            file = session.get(f'https://www.googleapis.com/drive/v3/files/{music["id"]}?alt=media')

            with open(pathlib.Path(music_dir, music['name']), 'wb') as stream:
                stream.write(file.content)

        subprocess.run(f'mpg123 --random {music_dir}/* &', shell=True)

    # Write our final credential information for use later.
    with open(credential_path, 'w') as stream:
        json.dump(json.loads(credentials.to_json()), stream)  # https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.to_json


if __name__ == '__main__':
    main()
