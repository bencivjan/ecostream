import sys, os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ffenc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ffenc_uiuc'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if ffenc_dir not in sys.path:
    sys.path.append(ffenc_dir)

import socket
import threading
import argparse
import time
import struct
from profiler import Profiler
from ffenc_uiuc import h264

def recv_client_video_thread(client_socket: socket.socket, addr: tuple, profiler: Profiler):
    client_ip = addr[0]

    streamer = h264.H264(client_socket)

    while True:
        try:
            frame = streamer.get_frame()
            if frame is None:
                raise ConnectionError
            
            profiler.add_frame(frame)

        except (ConnectionError, ConnectionResetError, BrokenPipeError):
            print("Client disconnected or error occurred")
            break

def profiling_thread(socket: socket.socket, profiler: Profiler, profiling_interval: int):
    socket_closed = threading.Event()

    bitrate = 5000

    while not socket_closed.is_set():
        time.sleep(profiling_interval)
        print(f'============ STARTING PROFILE =============')
        buffer_result = profiler.profile_buffer()
        print(f'============ BUFFER RESULT: {buffer_result} =============')

        fps = buffer_result

        threading.Thread(target=update_client_params,
                         kwargs={'socket':socket, 'fps':fps, 'bitrate':bitrate, 'shutdown':socket_closed}).start()
        
        # bitrate += 2000


def update_client_params(socket: socket.socket, fps: int, bitrate: int, shutdown: threading.Event):
    try:
        socket.sendall(struct.pack('!f', round(fps, 3)))
        socket.sendall(struct.pack('!I', bitrate))
    except (ConnectionError, ConnectionResetError, BrokenPipeError):
        shutdown.set()

def main():
    HOST_PUBLIC = '0.0.0.0'
    HOST_LOCAL = 'localhost'
    WEB_PORT = 8080

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--socket_port', type=int, default=8010)
    parser.add_argument('--profiling_interval', type=int, default=5)
    args = parser.parse_args()

    server_socket = socket.socket()
    server_socket.bind((HOST_PUBLIC, args.socket_port))
    server_socket.listen(1)
    # So we don't have to wait when restarting the server
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f'Starting server on port {args.socket_port}')

    video_profiler = Profiler(buffer_size=30)

    while True:
        client_socket, addr = server_socket.accept()

        threading.Thread(target=recv_client_video_thread,
                         kwargs={'client_socket':client_socket, 
                                 'addr': addr, 
                                 'profiler': video_profiler}).start()
        
        threading.Thread(target=profiling_thread,
                         kwargs={'socket': client_socket,
                                 'profiler': video_profiler,
                                 'profiling_interval': args.profiling_interval}).start()

if __name__ == '__main__':
    main()