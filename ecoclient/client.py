import sys, os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ffenc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ffenc_uiuc'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if ffenc_dir not in sys.path:
    sys.path.append(ffenc_dir)

import threading
import argparse
import time
import socket
import struct
import cv2
from ecoclient.video_processor import VideoProcessor
from ecoclient.utils import *
from ffenc_uiuc import h264

class EcoClient:
    def __init__(self, video_path, server_ip, server_port):
        self.video_path = video_path
        self.server_ip = server_ip
        self.server_port = server_port

        # Skip using locks here because of GIL, but if I ever switch to multiprocessing this will need a lock
        self.target_fps = 5.0
        self.shutdown = threading.Event()
        self.video_processor = None
        self.streamer = None
        self.cur_cpu_freq = MIN_CPU_FREQ

        # Throttle delay determines how many consecutive frames sent without throttling before we increase cpu frequency
        # Lower delay means the cpu frequency is more responsive but will use more power, higher delay means less responsive and less power
        self.throttle_delay = 15

        # Variables for evaluation
        self.frame_to_send = None
        self.save_path = None

    def start(self):
        client_socket = socket.socket()
        connect_socket(client_socket, self.server_ip, self.server_port)
        
        threading.Thread(target=self.send_video_thread,
                        kwargs={'socket': client_socket}).start()

        threading.Thread(target=self.recv_param_update_thread,
                        kwargs={'socket': client_socket}).start()
    
    def start_eval(self):
        client_socket = socket.socket()
        connect_socket(client_socket, self.server_ip, self.server_port)
        
        threading.Thread(target=self.evaluate_video_thread,
                        kwargs={'socket': client_socket}).start()

        threading.Thread(target=self.recv_param_update_thread,
                        kwargs={'socket': client_socket}).start()

    def send_video_thread(self, socket):
        adjusted_fps = self.target_fps
        throttle_count = 0

        set_cpu_freq(self.cur_cpu_freq)

        with VideoProcessor(self.video_path) as video:
            if not self.video_processor:
                self.video_processor = video

            self.streamer = h264.H264(socket, video.width, video.height, video.fps)
            for frame in video:
                start_time = time.time()
                self.streamer.send_frame(frame)

                if not throttle(adjusted_fps, start_time):
                    throttle_count += 1
                if throttle_count > self.throttle_delay:
                    self.cur_cpu_freq = min(MAX_CPU_FREQ, self.cur_cpu_freq + CPU_FREQ_DELTA)
                    set_cpu_freq(self.cur_cpu_freq)
                    throttle_count = 0

                adjusted_fps = recalibrate(self.target_fps, video.get_fps())

                print(f'FPS: {round(video.get_fps(), 3)}, Target FPS: {round(self.target_fps, 3)}, Adjusted FPS: {round(adjusted_fps, 3)}, Current CPU freq: {self.cur_cpu_freq}')
        
        print('Done streaming video...')
        self.shutdown.set()

    def evaluate_video_thread(self, socket):
        adjusted_fps = self.target_fps
        throttle_count = 0
        frames_sent = 0

        set_cpu_freq(self.cur_cpu_freq)

        if self.frame_to_send is None or self.save_path is None:
            raise AssertionError('Must set current frame and save path')
        
        self.streamer = h264.H264(socket, self.frame_to_send.shape[1], self.frame_to_send.shape[0], 30.0)

        self.eval_start_time = time.time()
        while self.frame_to_send is not None and self.save_path is not None:
            start_time = time.time()
            if not self.streamer.send_frame(self.frame_to_send, save_path=self.save_path):
                break
            frames_sent += 1

            if not throttle(adjusted_fps, start_time):
                throttle_count += 1
            if throttle_count > self.throttle_delay:
                self.cur_cpu_freq = min(MAX_CPU_FREQ, self.cur_cpu_freq + CPU_FREQ_DELTA)
                set_cpu_freq(self.cur_cpu_freq)
                throttle_count = 0

            adjusted_fps = recalibrate(self.target_fps, EcoClient.get_fps(self.eval_start_time, time.time(), frames_sent))

            print(f'FPS: {round(EcoClient.get_fps(self.eval_start_time, time.time(), frames_sent), 3)}, Target FPS: {round(self.target_fps, 3)}, Adjusted FPS: {round(adjusted_fps, 3)}, Current CPU freq: {self.cur_cpu_freq}')
        
        print('Done streaming video...')
        self.shutdown.set()

    def set_eval_params(self, frame_to_send, save_path):
        self.frame_to_send = frame_to_send
        self.save_path = save_path

    @staticmethod
    def get_fps(start_time, cur_time, num_frames):
        return num_frames / (cur_time - start_time)

    def recv_param_update_thread(self, socket: socket.socket):
        while not self.shutdown.is_set():
            fps = socket.recv(4)
            if not fps:
                return
            fps = struct.unpack('!f', fps)[0]
            bitrate = socket.recv(4)
            if not bitrate:
                return
            bitrate = struct.unpack('!I', bitrate)[0]
            
            self.target_fps = fps
            if self.video_processor is not None:
                self.video_processor.reset_fps_tracking()
            
            self.eval_start_time = time.time()

            set_cpu_freq(MIN_CPU_FREQ)
            self.streamer.encoder.change_settings(bitrate, 30) # Bitrate is in kb/s

            print(f'Setting to {fps} fps, {bitrate} bitrate')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server_ip', type=str, default='localhost')
    parser.add_argument('-p', '--server_port', type=int, default=8010)
    args = parser.parse_args()
    EcoClient('videos/crosswalk.avi', args.server_ip, args.server_port).start()