import os.path
import shutil
import configparser
import requests

# duplique le fichier de configuration par defaut
# si le fichier de configuration n'existe pas
if not os.path.isfile('config.ini'):
    print('Copy config from default...')
    shutil.copy2('config-default.ini','config.ini')
    print('Done.')

# charge le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')
print('Server Url : '+config['master']['url'])

# variables
url = config['master']['url']+'post'
mod_id = config['module']['id']

# fichiers images
files = [
    ('a', ('test-a.jpg',open('test-a.jpg', 'rb'), 'image/jpg')),
    ('b', ('test-b.jpg',open('test-b.jpg', 'rb'), 'image/jpg'))
    ]
# headers HTTP applicatif
headers = {'x-mod-id': mod_id}

r = requests.post(url, files=files, headers=headers)
print(r.text)