import sys
import threading
import argparse
import time
from datetime import datetime
import socket
import subprocess
import struct
from video_processor import VideoProcessor

sys.path.append('ffenc_uiuc')
from ffenc_uiuc import h264

def connect_socket(sock: socket.socket, args):
    while True:
        try:
            sock.connect((args.server_ip, args.server_port))
            break
        except OSError:
            print("Unable to connect to server socket, retrying...")
            datetime_obj = datetime.fromtimestamp(time.time())
            readable_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
            with open("errors.out", "a") as err_file:
                err_file.write(f'{readable_time}: Unable to connect to server at {args.server_ip}\n')
            time.sleep(5)

# Scaling governor must be set to userspace
# `sh -c 'sudo cpufreq-set -g userspace'`
def set_cpu_freq(cpu_freq):
    with open('/sys/devices/system/cpu/cpufreq/policy0/scaling_governor', 'r') as file:
        assert file.read().strip() == 'userspace', 'Scaling governor must be set to userspace\n`sudo cpufreq-set -g userspace`'
    
    cpu_freq = str(cpu_freq)
    print(f'Setting cpu freqency to {cpu_freq} KHz')

    command = f"echo {cpu_freq} | sudo tee /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    if result.returncode == 0:
        print("Successfully set cpu frequency")
    else:
        print("Failed to set cpu frequency")
        print(f"Error: {result.stderr}")

def throttle(target_fps, start_time):
    # Calculate the time to wait between frames
    frame_time = 1.0 / target_fps

    elapsed_time = time.time() - start_time
    time_to_wait = frame_time - elapsed_time
    if time_to_wait > 0:
        time.sleep(time_to_wait)

def send_video_thread(socket):
    target_fps = 5

    with VideoProcessor('videos/ny_driving.mov') as video:
        streamer = h264.H264(socket, video.width, video.height, video.fps)
        for frame in video:
            start_time = time.time()
            streamer.send_frame(frame)
            throttle(target_fps, start_time)

        print(f'FPS: {video.get_fps()}')

def recv_param_update_thread(socket: socket.socket):
    while True:
        fps = socket.recv(4)
        if not fps:
            return
        fps = struct.unpack('!I', fps)[0]
        bitrate = socket.recv(4)
        if not bitrate:
            return
        bitrate = struct.unpack('!I', bitrate)[0]
        print(f'Setting to {fps} fps, {bitrate} bitrate')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server_ip', type=str, default='localhost')
    parser.add_argument('-p', '--server_port', type=int, default=8010)
    args = parser.parse_args()

    client_socket = socket.socket()
    # client_socket.settimeout(5)  # 5 seconds timeout
    connect_socket(client_socket, args)
    
    threading.Thread(target=send_video_thread,
                     kwargs={'socket': client_socket}).start()
    
    threading.Thread(target=recv_param_update_thread,
                     kwargs={'socket': client_socket}).start()

if __name__ == '__main__':
    main()