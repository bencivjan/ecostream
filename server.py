import socket
import threading
import argparse
import sys
import time
from profiler import Profiler

sys.path.append('ffenc_uiuc')
from ffenc_uiuc import h264

def recv_client_video_thread(client_socket: socket, addr: tuple, profiler: Profiler):
    print('A')
    client_ip = addr[0]
    # print(f'client ip: {client_ip}')

    streamer = h264.H264(client_socket)

    while True:
        try:
            frame = streamer.get_frame()
            if frame is None:
                raise ConnectionResetError
            
            profiler.add_frame(frame)

        except (ConnectionResetError, BrokenPipeError):
            print("Client disconnected or error occurred")
            break

def profiling_thread(profiler: Profiler, profiling_interval: int):
    while True:
        time.sleep(profiling_interval)
        buffer_result = profiler.profile_buffer()
        print(f'============ BUFFER RESULT: {buffer_result} =============')

def update_client_params_thread(socket, addr):
    print('C')
    # while True:
    #     data = socket.send(1024)

def main():
    HOST_PUBLIC = '0.0.0.0'
    HOST_LOCAL = 'localhost'
    WEB_PORT = 8080

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--socket_port', type=int, default=8010)
    args = parser.parse_args()

    server_socket = socket.socket()
    server_socket.bind((HOST_LOCAL, args.socket_port))
    server_socket.listen(1)
    # So we don't have to wait when restarting the server
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f'Starting server on port {args.socket_port}')

    video_profiler = Profiler()

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=recv_client_video_thread, kwargs={'client_socket':client_socket, 
                                                                  'addr': addr, 
                                                                  'profiler': video_profiler}).start()
        threading.Thread(target=profiling_thread, kwargs={'profiler': video_profiler,
                                                          'profiling_interval': 30}).start()
        threading.Thread(target=update_client_params_thread, kwargs={'socket':client_socket,
                                                                     'addr': addr}).start()

    # Join threads?

if __name__ == '__main__':
    main()