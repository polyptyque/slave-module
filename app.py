#!/usr/bin/python3
print("\n------ POLYPTYQUE ------")
print("slave-module démarre ...\n")
import os.path
import shutil
import configparser
import socket
import requests
import time
import io
import json

rootPath = os.path.dirname(os.path.abspath(__file__))
#os.path.dirname(rootpath)
print("setting up root path :", rootPath)
os.chdir(rootPath)

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
post_url = master_base_url + '/post'
config_url = master_base_url + '/config'
mod_id = config['module']['id']
udp_port = int(config['udp']['port'])
cam_count = int(config['camera']['count'])
cam_width = int(config['camera']['width'])
cam_height = int(config['camera']['height'])
cam_preview = config['camera']['preview'] == 'yes'
cam_0_rotation = int(config['camera']['rotation_0'])
cam_1_rotation = int(config['camera']['rotation_1'])

print('Slave module id : ', mod_id)
print('Run mode : ', runmode)
print('Cam count : ', cam_count)
print('Server Url : ' + master_base_url)


def save_config():
    global config
    config_file = open("config.ini", "w")
    config.write(config_file)
    print("config saved")


def update_master_configuration(options):
    global config, master_hostname, master_base_url, post_url, config_url
    if options['hostname'] is not None:
        master_hostname = options['hostname']
        config['master']['hostname'] = master_hostname
    master_base_url = 'http://' + master_hostname + ':' + master_port
    post_url = master_base_url + '/post'
    config_url = master_base_url + '/config'
    print("master hostname updated to " + master_base_url)
    save_config()


def init_camera_options(id, rotation):

    # Resolution
    resolution = picamera.PiResolution(cam_width, cam_height)

    # Start the camera
    camera = picamera.PiCamera(id)#, 'none', False, resolution, 1)

    # Rotation
    camera.rotation = rotation

    # Exposure
    #camera.exposure_mode = 'off'

    # Automatic White balance
    #camera.awb_mode = 'off'
    #print(camera.awb_gains)
    #camera.awb_gains = (0.9,2.9)

    # Camera resolution
    camera.resolution = '1080x1920'

    # Led off
    camera.led = 0

    # Update camera options
    update_camera_options(camera)

    return camera


def update_camera_options(camera):

    # Iso
    camera.iso = 400

    # Brightness
    camera.brightness = 50

    # Contrast
    camera.contrast = 0

    # Saturation
    camera.saturation = 0

    # Sharpness
    camera.sharpness = 0

    # shutter_speed
    # camera.shutter_speed


def get_camera_options():
    global config, mod_id
    # envoie au master les options de configuration camera

    # headers
    headers = {
        'content-type': 'application/json',
	'x-from': 'cm'+mod_id,
        'x-action': 'get_camera_options'
    }

    camera_options = json.loads(json.dumps(dict(config.items('camera'))))
    print('get_camera_options post',camera_options)
    r = requests.post(config_url, json=camera_options, headers=headers)
    print(r.text)
	


def set_camera_options(options):
    global config

    print('options', options)

if not simulation:
    import picamera

    # initialise la camera 0
    camera0 = init_camera_options(0, cam_0_rotation)

    # initialise la camera 1
    if cam_count > 1:
        camera1 = init_camera_options(1, cam_1_rotation)

    # lance la preview camera
    if cam_preview:
        print("Start camera preview")
        camera0.start_preview()


def sendimages(id):
    global post_url
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
        'x-cam-count': cam_count,
        'x-shot-id': id
    }

    r = requests.post(post_url, files=files, headers=headers)
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
    if message['action'] == 'shot':
        print("shot", message['id'])
        takeimages(message['id'])
    elif message['action'] == 'update_master_configuration':
        update_master_configuration(message)
    elif message['action'] == 'get_camera_options':
        get_camera_options()
    elif message['action'] == 'set_camera_options':
        set_camera_options(message['options'])
    else:
        print("action inconnue")
