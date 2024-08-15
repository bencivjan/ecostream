import cv2
import time
import os

class VideoProcessor:

    def __init__(self, video_path):
        if not os.path.isfile(video_path):
            raise FileNotFoundError('Invalid file path')
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.frame_count = self.cap.get(int(cv2.CAP_PROP_FRAME_COUNT))

        self._index = 0

        # Record FPS
        self.total_time = 0
        self._previous_time = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cap.release()

    def release(self):
        self.cap.release()

    def __iter__(self):
        return self

    def __next__(self):
        if self._previous_time == 0:
            self._previous_time = time.time()

        self._ret, self._frame = self.cap.read()

        if not self._ret:
            raise StopIteration

        cur_time = time.time()
        self.total_time += (cur_time - self._previous_time)
        self._previous_time = cur_time

        self._index += 1
        return self._frame

    def __len__(self):
        return self.frame_count
    
    def get_fps(self):
        return self._index / self.total_time if self.total_time > 0 else 0
    
    def reset_fps_tracking(self):
        self._previous_time = time.time()
        self.total_time = 0
        self._index = 0