import os.path
import shutil
import configparser
import socket
import requests
import time
import io
import json

# duplique le fichier de configuration par défaut
# si le fichier de configuration n'existe pas
if not os.path.isfile('config.ini'):
    print('Copy config from default...')
    shutil.copy2('config-default.ini', 'config.ini')
    print('Done.')

# charge le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# variables par défaut
runmode = config['app']['runmode']
simulation = runmode == "simulation"
master_hostname = config['master']['hostname']
master_port = config['master']['port']
master_base_url = 'http://' + master_hostname + ':' + master_port
url = master_base_url + '/post'
mod_id = config['module']['id']
udp_port = int(config['udp']['port'])

print('Slave module id : ', mod_id)
print('Run mode : ', runmode)
print('Server Url : ' + master_base_url)


def update_master_configuration(options):
    global config, master_hostname, master_base_url
    if options['hostname'] is not None:
        master_hostname = options['hostname']
        config['master']['hostname'] = master_hostname
    master_base_url = 'http://' + master_hostname + ':' + master_port
    config.write('config.ini')
    print("master hostname updated to " + master_base_url)


def updatemasterdata(h, p):
    global master_hostname
    # update datas from master UDP configuration
    master_base_url = 'http://' + h + ':' + p
    url = master_base_url + '/post'


if not simulation:
    import picamera

    # declare la camera
    camera0 = picamera.PiCamera(0)
    camera1 = picamera.PiCamera(1)
    # lance la camera
    # camera0.start_preview()
    # camera1.start_preview()


def sendimages(id):
    # fichiers images

    filename0 = id + '-0.jpg'
    filename1 = id + '-1.jpg'
    if not simulation:
        src0 = filename0
        src1 = filename1
    else:
        src0 = 'test-a.jpg'
        src1 = 'test-b.jpg'

    print("open ", src0, "and", src1)
    files = [
        ('a', (filename0, open(src0, 'rb'), 'image/jpg')),
        ('b', (filename1, open(src1, 'rb'), 'image/jpg'))
    ]
    # headers HTTP applicatif
    headers = {
        'x-run-mod': runmode,
        'x-mod-id': mod_id,
        'x-shot-id': id
    }

    r = requests.post(url, files=files, headers=headers)
    print(r.text)


def takeimages(id):
    if not simulation:
        t = time.strftime('%Y-%m-%d_%H-%M-%S')
        a = time.clock()
        stream0 = io.BytesIO()
        stream1 = io.BytesIO()

        # print("capture camera 0", time.clock())
        # f0 = camera0.capture_continuous(stream0, format='jpeg', use_video_port=False)
        # print("capture camera 1", time.clock())
        # f1 = camera1.capture_continuous(stream1, format='jpeg', use_video_port=False)
        # print("ok",time.clock());

        # savejpegstream(0,stream0);
        # savejpegstream(1,stream1);

        camera0.capture(id + '-0.jpg', format='jpeg')
        camera1.capture(id + '-1.jpg', format='jpeg')

        b = time.clock()
        print('image shot in ' + str(round((b - a) * 1000)) + 'ms ')

    sendimages(id)


# serveur UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', udp_port))
print("bind socket on port " + str(udp_port))

while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    print("received message:" + str(type(data)))
    message = json.loads(data.decode('utf-8'))
    print(addr)
    action = message['action']
    if action == 'shot':
        print("shot", message['id'])
        takeimages(message['id'])
    elif action == 'update_master_configuration':
        update_master_configuration(message)
    else:
        print("action inconnue")
