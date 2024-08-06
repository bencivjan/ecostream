import time
import ffdec
import ffenc
import numpy as np
import cv2
import struct
import datetime

class H264:
    def __init__(self, sock, w=1, h=1, fps=1, logger=None):
        self.sock = sock
        self.logger = logger
        self.encoder = ffenc.ffenc(int(w), int(h), int(fps))
        self.decoder = ffdec.ffdec()
        self.buffer = b''
        self.send_frame_idx = 0
        self.recv_frame_idx = 0
        self.nbytes_received = 0

        # print(w, h, fps)
        # self.encoder.change_settings(5000, 30)


    def send_frame(self, frame):
        try:
            out = self.encoder.process_frame(frame)

            # print(f'Frame size: {out.shape[0]} bytes')
            start_time = time.time()

            self.sock.sendall(struct.pack('!d', start_time))
            self.sock.sendall(struct.pack('!I', out.shape[0]))
            self.sock.sendall(out.tobytes())
            end_time = time.time()

            log = {}

            log['frame'] = self.send_frame_idx
            log['client_send_start_time'] = start_time
            log['client_send_end_time'] = end_time
            log['client_send_duration'] = f'{end_time - start_time:.4f}'

            if self.logger:
                self.logger.log(log)
            self.send_frame_idx += 1
        except TimeoutError:
            print("Unable to send frame, connection timed out...")
            if self.logger:
                datetime_obj = datetime.fromtimestamp(time.time())
                readable_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
                self.logger.log({
                    'Connection timed out': readable_time
                })
        
    def get_frame(self):
        """
        Decodes and returns an h264 frame from the socket

        Parameters:
        - None

        Returns:
        - The received frame bytes or None if client has disconnected
        """
        start_time_bytes = self.sock.recv(8)
        if not start_time_bytes:
            return
        client_send_start_time = struct.unpack('!d', start_time_bytes)[0]

        data_length_bytes = self.sock.recv(4)
        if not data_length_bytes:
            return
        data_length = struct.unpack('!I', data_length_bytes)[0]
        
        server_recv_start_time = time.time()

        while len(self.buffer) < data_length:
            data = self.sock.recv(min(data_length - len(self.buffer), 40960))
            if not data: # socket closed
                return None
            self.buffer += data

        self.nbytes_received += len(self.buffer)

        server_recv_end_time = time.time()

        data = np.frombuffer(self.buffer, dtype=np.uint8)
        print(data.nbytes)
        frame = self.decoder.process_frame(data)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.buffer = b''

        log = {}

        network_duration = server_recv_end_time - client_send_start_time
        bandwidth = data_length / network_duration

        log['frame'] = self.recv_frame_idx
        log['frame_size'] = f'{data_length / 1000} KB'
        log['client_send_start_time'] = client_send_start_time
        log['server_recv_start_time'] = server_recv_start_time
        log['server_recv_end_time'] = server_recv_end_time
        log['server_recv_duration'] = server_recv_end_time - server_recv_start_time
        log['network_duration'] = f'{network_duration * 1000:.4f} ms'
        log['bandwidth'] = f'{(bandwidth * 8) / (1000 * 1000):.4f} Mbps'

        if self.logger:
            self.logger.log(log)
        self.recv_frame_idx += 1

        return frame