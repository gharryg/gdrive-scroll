import os
from time import sleep
import pickle
import google_auth_oauthlib
from google.auth.transport.requests import AuthorizedSession
from google.auth.exceptions import RefreshError
import sys
import shutil
import subprocess

# https://console.developers.google.com/apis/credentials for CLIENT_ID and CLIENT_SECRET
CLIENT_ID = 'FOO'
CLIENT_SECRET = 'FOO'
# https://developers.google.com/drive/api/v3/about-auth
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PARENT_ID = 'FOO'
API_ROOT = 'https://www.googleapis.com/drive/v3'
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CREDENTIALS_PATH = '%s/credentials.pickle' % DIR_PATH
IMAGES_PATH = '%s/images' % DIR_PATH


def rolling_slides():
    # https://google-auth.readthedocs.io/en/latest/user-guide.html#user-credentials
    # https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.html
    # check access_token status: https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=[TOKEN]
    # load credentials object from pickle
    if os.path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH, 'rb') as f:
            credentials = pickle.load(f)
    else:
        # fetch new credentials
        credentials = google_auth_oauthlib.get_user_credentials(SCOPES, CLIENT_ID, CLIENT_SECRET)

    # create google-auth requests session; this will handle token refresh and checking
    # https://google-auth.readthedocs.io/en/latest/reference/google.auth.transport.requests.html#google.auth.transport.requests.AuthorizedSession
    session = AuthorizedSession(credentials)

    # https://developers.google.com/drive/api/v3/reference/files/list
    # https://developers.google.com/drive/api/v3/search-files
    files = session.get('%s/files?supportsAllDrives=true&includeItemsFromAllDrives=true&q=\'%s\' in parents and trashed = false' % (API_ROOT, PARENT_ID))
    # if this doesn't work, a RefreshError will be raised the DC logo will be shown

    if not files.ok:
        files.raise_for_status()

    # see if there are existing images; if so, remove the images directory and its content then create a new directory
    if os.path.exists(IMAGES_PATH):
        shutil.rmtree(IMAGES_PATH)
    # we make the directory in both cases, whether it isn't there or when we remove it
    os.mkdir(IMAGES_PATH)

    # example file response:
    #  {
    #   "kind": "drive#file",
    #   "id": "FOO",
    #   "name": "FOO",
    #   "mimeType": "image/jpeg"
    #  }

    # we don't want files that aren't images
    images = [file for file in files.json()['files'] if file['mimeType'].startswith('image')]

    for image in images:
        # https://developers.google.com/drive/api/v3/reference/files/get
        file = session.get('%s/files/%s?alt=media' % (API_ROOT, image['id']))

        with open('%s/%s' % (IMAGES_PATH, image['name']), 'wb') as f:
            f.write(file.content)

    # store credentials so we don't have to re-authenticate next execution
    with open(CREDENTIALS_PATH, 'wb') as f:
        pickle.dump(credentials, f)

    # collect images paths and start the scroll
    image_paths = ['"%s/%s"' % (IMAGES_PATH, image['name']) for image in images]
    subprocess.run('/usr/bin/fbi -noverbose -a -T 1 -t 10 %s' % ' '.join(image_paths), shell=True)


if __name__ == '__main__':
    try:
        rolling_slides()
    except Exception:  # if we hit any exception, just show the DC logo
        subprocess.run('/usr/bin/fbi -noverbose -a -T 1 %s/dc.png' % DIR_PATH, shell=True)
