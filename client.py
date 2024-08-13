import sys
import threading
import argparse
import time
import socket
import struct
from ecoclient.video_processor import VideoProcessor
from ecoclient.utils import connect_socket, set_cpu_freq, throttle, recalibrate

sys.path.append('ffenc_uiuc')
from ffenc_uiuc import h264

MIN_CPU_FREQ = 1500000
MAX_CPU_FREQ = 2400000
CPU_FREQ_DELTA = 300000

# Skip using locks here because of GIL, but if I ever switch to multiprocessing this will need a lock
target_fps = 5.0
shutdown = threading.Event()
video_processor = None
cur_cpu_freq = MIN_CPU_FREQ

def send_video_thread(socket):
    global target_fps, video_processor, cur_cpu_freq
    adjusted_fps = target_fps

    # Throttle delay determines how many consecutive frames sent without throttling before we increase cpu frequency
    # Lower delay means the cpu frequency is more responsive but will use more power, higher delay means less responsive and less power
    throttle_delay = 15
    throttle_count = 0

    set_cpu_freq(cur_cpu_freq)

    with VideoProcessor('videos/ny_driving.mov') as video:
        if not video_processor:
            video_processor = video

        streamer = h264.H264(socket, video.width, video.height, video.fps)
        for frame in video:
            start_time = time.time()
            streamer.send_frame(frame)

            if not throttle(adjusted_fps, start_time):
                throttle_count += 1
            if throttle_count > throttle_delay:
                cur_cpu_freq = min(MAX_CPU_FREQ, cur_cpu_freq + CPU_FREQ_DELTA)
                set_cpu_freq(cur_cpu_freq)
                throttle_count = 0

            adjusted_fps = recalibrate(target_fps, video.get_fps())

            print(f'FPS: {round(video.get_fps(), 3)}, Target FPS: {round(target_fps, 3)}, Adjusted FPS: {round(adjusted_fps, 3)}, Current CPU freq: {cur_cpu_freq}')
    
    print('Done streaming video...')
    shutdown.set()

def recv_param_update_thread(socket: socket.socket):
    global target_fps, video_processor
    
    while not shutdown.is_set():
        fps = socket.recv(4)
        if not fps:
            return
        fps = struct.unpack('!f', fps)[0]
        bitrate = socket.recv(4)
        if not bitrate:
            return
        bitrate = struct.unpack('!I', bitrate)[0]
        
        target_fps = fps
        if video_processor is not None:
            video_processor.reset_fps_tracking()

        set_cpu_freq(MIN_CPU_FREQ)

        print(f'Setting to {fps} fps, {bitrate} bitrate')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server_ip', type=str, default='localhost')
    parser.add_argument('-p', '--server_port', type=int, default=8010)
    args = parser.parse_args()

    client_socket = socket.socket()
    connect_socket(client_socket, args)
    
    threading.Thread(target=send_video_thread,
                     kwargs={'socket': client_socket}).start()

    threading.Thread(target=recv_param_update_thread,
                     kwargs={'socket': client_socket}).start()

if __name__ == '__main__':
    main()