import os.path
import shutil
import configparser
import socket
import requests
import picamera
import time
import io

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
master_base_url = 'http://'+config['master']['hostname']+':'+config['master']['port']
url = master_base_url+'/post'
mod_id = config['module']['id']
ip_master = config['udp']['ip_master']
udp_port = int(config['udp']['port'])
print('Server Url : '+master_base_url)

# declare la camera
camera0 = picamera.PiCamera(0)
camera1 = picamera.PiCamera(1)
# lance la camera
#camera0.start_preview()
#camera1.start_preview()

def sendimages(prefix):
    # fichiers images
    files = [
        ('a', (prefix+'0.jpg',open(prefix+'0.jpg', 'rb'), 'image/jpg')),
        ('b', (prefix+'1.jpg',open(prefix+'1.jpg', 'rb'), 'image/jpg'))
        ]
    # headers HTTP applicatif
    headers = {'x-mod-id': mod_id,'x-img-prefix':prefix}

    r = requests.post(url, files=files, headers=headers)
    print(r.text)

   

def takeimages():
    t = time.strftime('%Y-%m-%d_%H-%M-%S')
    a = time.clock()
    stream0 = io.BytesIO()
    stream1 = io.BytesIO()
    
    #print("capture camera 0", time.clock())
    #f0 = camera0.capture_continuous(stream0, format='jpeg', use_video_port=False)
    #print("capture camera 1", time.clock())
    #f1 = camera1.capture_continuous(stream1, format='jpeg', use_video_port=False)
    #print("ok",time.clock());
    
    #savejpegstream(0,stream0);
    #savejpegstream(1,stream1);

    img_prefix = 'img-'+t+'-cam-'
    camera0.capture(img_prefix+'0.jpg', format='jpeg')
    camera1.capture(img_prefix+'1.jpg', format='jpeg')

    b = time.clock()
    print('image shot in '+str(round((b-a)*1000))+'ms ')
    sendimages(img_prefix)

# serveur UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', udp_port))
print("bind socket on port "+str(udp_port))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message:"+str(type(data)))
    print(addr)
    print(data)
    takeimages()
