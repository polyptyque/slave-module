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


def save_config():
    global config
    config_file = open("config.ini", "w")
    config.write(config_file)
    print("config saved")

# config default upgrade


def defaut_config_init(reset=False):
    config_default = configparser.ConfigParser()
    config_default.read('config-default.ini')
    # camera tcp default
    if not config.has_section('tcp'):
        config.add_section('tcp')
        config.set('tcp', 'port', config_default.get('tcp', 'port'))
        save_config()
    # camera config
    if not config.has_section('camera'):
        config.add_section('camera')
    config_default_camera_options = json.loads(json.dumps(dict(config_default.items('camera'))))
    for key, value in config_default_camera_options.items():
        try:
            config_key_value = config.get('camera', key)
            if reset:
                config.set('camera', key, value)
                print("\t camera ", key, value, '(reset)')
            else:
                print("\t camera ", key, config_key_value)
        except:
            print("\t camera ", key, value, '(default)')
            config.set('camera', key, value)
    if reset:
        print("Reset and exit")
        save_config()
        quit()

defaut_config_init()

# camera
camera0 = None
camera1 = None

# camera stream
stream0 = None
stream1 = None

# est-ce que la prise de vue est "en cours"
shooting = False

# variables par défaut
try:
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
    cam_preview_started = False
    cam_0_rotation = int(config['camera']['rotation_0'])
    cam_1_rotation = int(config['camera']['rotation_1'])
    camera_auto = config['camera']['auto'] == 'on'
    use_video_port = config.get('camera', 'use_video_port') == 'on'
    jpeg_quality = int(config.get('camera', 'jpeg_quality'))
    cache_path = 'cache/'
    tcp_port = int(config['tcp']['port'])
    is_master = mod_id == 0
except:
    defaut_config_init(reset=True)

print('Slave module id : ', mod_id)
print('Run mode : ', runmode)
print('Cam count : ', cam_count)
print('Server Url : ' + master_base_url)


#
# UPDATE MASTER CONFIGURATION
#


def update_master_configuration(options):
    global config, master_hostname, master_port, master_base_url, post_url, config_url
    if options['hostname'] is not None:
        master_hostname = options['hostname']
        config['master']['hostname'] = master_hostname
    if options['port'] is not None:
        master_port = options['port']
        config['master']['port'] = master_port
    master_base_url = 'http://' + master_hostname + ':' + master_port
    post_url = master_base_url + '/post'
    config_url = master_base_url + '/config'
    print("master hostname updated to " + master_base_url)
    save_config()


#
# INIT CAMERA OPTIONS
#


def init_camera_options(cam_id, rotation):

    # Resolution
    #resolution = picamera.PiResolution(cam_width, cam_height)

    # Start the camera
    camera = picamera.PiCamera(camera_num=cam_id)

    # Rotation
    camera.rotation = rotation

    # Update camera options
    update_camera_options(camera)

    return camera


#
# UPDATE CAMERA OPTIONS
#


def update_camera_options(camera):
    global camera_auto
    # si la caméra n'existe pas, on n'essaie même pas
    if camera is None:
        return

    # Horizontal flip
    camera.hflip = True

    # Camera resolution
    camera.resolution = (cam_width, cam_height)

    # Led off (requiert GPIO lib)
    # camera.led = 0

    # mode automatique
    if camera_auto:
        print('Mode automatique')
        # Exposure
        camera.exposure_mode = 'auto'

        # Automatic White balance
        camera.awb_mode = 'auto'

        return
    else:
        # Exposure
        camera.exposure_mode = 'off'

        # Automatic White balance
        camera.awb_mode = 'off'

        # Camera resolution
        camera.resolution = (cam_width, cam_height)

        # Led off
        # camera.led = 0


    # Iso
    camera.iso = int(config.get('camera', 'iso'))

    # Shutter speed
    camera.shutter_speed = int(config.get('camera', 'shutter_speed'))

    # Exposure compensation
    camera.exposure_compensation = int(config.get('camera', 'exposure_compensation'))

    # Brightness
    camera.brightness = int(config.get('camera', 'brightness'))

    # Contrast
    camera.contrast = int(config.get('camera', 'contrast'))

    # Saturation
    camera.saturation = int(config.get('camera', 'saturation'))

    # Sharpness
    camera.sharpness = int(config.get('camera', 'sharpness'))

    # AWB
    camera.awb_gains = (float(config.get('camera', 'awb_gain_red')), float(config.get('camera', 'awb_gain_blue')))

    if camera.preview:
        print("camera.preview.window", camera.preview.window)
        print("camera.preview.crop", camera.preview.crop)

#
# GET STATUS
#


def get_status():
    global config, mod_id
    # headers
    headers = {
        'content-type': 'application/json',
        'x-from': 'cm' + mod_id,
        'x-action': 'get_status'
    }

    print('get_status')
    status = {"status": "ok", "mod_id": mod_id}
    try:
        requests.post(config_url, json=status, headers=headers)
    except:
        print('HTTP request error (get_status)')
#
# RESET SHOOTING TO INITIAL STATE
#


def reset_shooting():
    global shooting
    shooting = False

#
# GET CAMERA OPTIONS
#


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
    try:
        requests.post(config_url, json=camera_options, headers=headers)
    except:
        print('HTTP request error (get_camera_options)')
#
# SET CAMERA OPTIONS
#


def set_camera_options(options):
    global config, camera0, camera1, camera_auto, jpeg_quality, use_video_port

    print('Update Camera options to ')
    for key, value in options.items():
        if value:
            print("\t"+key+" : "+value)
            config.set('camera', key, value)

    camera_auto = config.get('camera', 'auto') == 'on'
    print('camera_auto quality', camera_auto)

    jpeg_quality = int(config.get('camera', 'jpeg_quality'))
    print('Jpeg quality', jpeg_quality)

    use_video_port = config.get('camera', 'use_video_port') == 'on'
    print('use_video_port', use_video_port)

    update_camera_options(camera0)
    update_camera_options(camera1)
    save_config()


#
# Camera startup
#

if not simulation:
    import picamera


def startcamera():
    global camera0, camera1
    if not simulation:
        print("Camera starts...")

        # on arrete la preview si on redémarre
        if cam_preview:
            if camera0:
                print("Stop Preview")
                camera0.stop_preview()
                time.sleep(5)

        print("Camera 0 start")

        # initialise la camera 0
        camera0 = init_camera_options(0, cam_0_rotation)

        # initialise la camera 1
        if cam_count > 1:
            print("Camera 1 start")
            camera1 = init_camera_options(1, cam_1_rotation)

        # lance la preview camera
        if cam_preview:
            print("Start camera 0 preview")
            cam_preview_started = True
            camera0.start_preview()


# initial start
startcamera()

#
# Toggle Preview
#


def toggle_preview():
    global cam_preview_started, cam_preview
    if cam_preview:
        if cam_preview_started:
            print('Toggle Off preview')
            camera0.stop_preview()
            cam_preview_started = False
        else:
            print('Toggle On preview')
            camera0.start_preview()
            cam_preview_started = True

#
# Confirmation de la prise de vue
#


def confirm_shoot(uid, success):
    global post_url
    headers = {
        'x-run-mod': runmode,
        'x-mod-id': mod_id,
        'x-cam-count': str(cam_count),
        'x-shot-uid': uid,
        'x-action': 'confirm_shot',
        'x-status': 'ok' if success else 'fail'
    }

    print("confirm shot...")
    try:
        r = requests.post(post_url, headers=headers)
        print(r.text)
    except:
        print('HTTP request error (confirm_shoot)')

#
# SEND IMAGES
#


def send_images(uid):
    global post_url, shooting
    # fichiers images

    filename0 = uid + '-0.jpg'
    filename1 = uid + '-1.jpg'
    if not simulation:
        src0 = cache_path+filename0
        src1 = cache_path+filename1
    else:
        src0 = 'test-a.jpg'
        src1 = 'test-b.jpg'

    if cam_count > 1:
        # mode stereo
        print("open stereo", src0, "and", src1)
        files = [
            ('a', (filename0, open(src0, 'rb'), 'image/jpg')),
            ('b', (filename1, open(src1, 'rb'), 'image/jpg'))
        ]
    else:
        # mode mono
        print("open mono", src0)
        files = [
            ('a', (filename0, open(src0, 'rb'), 'image/jpg')),
        ]
    # headers HTTP applicatif
    headers = {
        'x-run-mod': runmode,
        'x-mod-id': mod_id,
        'x-cam-count': str(cam_count),
        'x-shot-uid': uid,
        'x-action': 'send_image'
    }

    try:
        requests.post(post_url, files=files, headers=headers)
        print("Upload success.")
    except:
        print('HTTP request error (image upload)')
    finally:
        shooting = False


def savejpegstream(uid, cam_id, stream):
    global cache_path
    if stream:
        print("save jpeg stream for camera", cam_id, 'uid', uid)
        print(time.clock())
        jpeg_path = cache_path+uid+'-'+str(cam_id)+'.jpg'
        print("open", jpeg_path, "...")
        with io.open(jpeg_path, 'wb') as jpeg_file:
            jpeg_file.write(stream.getvalue())
            print("write done.")
            jpeg_file.close()
        return True
    else:
        return False


def takeimages(uid):
    global shooting, stream0, stream1

    # Si on est en cours de prise de vue, on attend
    if shooting:
        confirm_shoot(uid, False)
        return

    # Oui, les cameras font des prises de vues !
    shooting = True

    if not simulation:
        # t = time.strftime('%Y-%m-%d_%H-%M-%S')
        a = time.clock()

        # print("capture camera 0", time.clock())
        # f0 = camera0.capture_continuous(stream0, format='jpeg', use_video_port=False)
        # print("capture camera 1", time.clock())
        # f1 = camera1.capture_continuous(stream1, format='jpeg', use_video_port=False)
        # print("ok",time.clock());
        print('takeimages', a)

        if camera0:
            stream0 = io.BytesIO()
            camera0.capture(stream0, format='jpeg', quality=jpeg_quality, use_video_port=use_video_port)
            print('Camera Capture 0', time.clock())

        if camera1:
            stream1 = io.BytesIO()
            camera1.capture(stream1, format='jpeg', quality=jpeg_quality, use_video_port=use_video_port)
            print('Camera Capture 1', time.clock())

        if camera0:
            savejpegstream(uid, 0, stream0)

        if camera1:
            savejpegstream(uid, 1, stream1)

        # static camera shoot in file
        # if camera0:
        #    camera0.capture(cache_path+id + '-0.jpg', format='jpeg')
        # if camera1:
        #    camera1.capture(cache_path+id + '-1.jpg', format='jpeg')

        b = time.clock()
        print('image shot in ' + str(round((b - a) * 1000)) + 'ms ')

    confirm_shoot(uid, True)
    # send_images(uid)


# serveur UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('', udp_port))
print("bind socket on port " + str(udp_port))

# Exit
import atexit


def appexit():
    global cam_preview_started
    if cam_preview:
        print("Stop Preview")
        camera0.stop_preview()
        cam_preview_started = False

atexit.register(appexit)

#
# UDP server
#


while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    message = json.loads(data.decode('utf-8'))
    print("received message, from ", addr, ':')
    print(message)
    if message['action'] == 'shot':
        print("shot", message['uid'])
        takeimages(message['uid'])
    elif message['action'] == 'send_images':
        send_images(message['uid'])
    elif message['action'] == 'update_master_configuration':
        update_master_configuration(message)
    elif message['action'] == 'restart_camera':
        startcamera()
    elif message['action'] == 'toggle_preview':
        toggle_preview()
    elif message['action'] == 'get_status':
        get_status()
    elif message['action'] == 'reset_shooting':
        reset_shooting()
    elif message['action'] == 'get_camera_options':
        get_camera_options()
    elif message['action'] == 'set_camera_options':
        set_camera_options(message['options'])
    else:
        print("action inconnue")
