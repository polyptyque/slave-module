import os.path
import shutil
import configparser
import socket
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

# variables
url = 'http://'+config['master']['hostname']+'/post'
mod_id = config['module']['id']
ip_master = config['udp']['ip_master']
udp_port = int(config['udp']['port'])
print('Server Url : '+url)

def sendimages():
    # fichiers images
    files = [
        ('a', ('test-a.jpg',open('test-a.jpg', 'rb'), 'image/jpg')),
        ('b', ('test-b.jpg',open('test-b.jpg', 'rb'), 'image/jpg'))
        ]
    # headers HTTP applicatif
    headers = {'x-mod-id': mod_id}

    r = requests.post(url, files=files, headers=headers)
    print(r.text)

# serveur UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', udp_port))
print("bind socket on port "+str(udp_port))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message:"+str(type(data)))
    print(addr)
    print(data)