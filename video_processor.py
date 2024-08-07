import cv2
import time

class VideoProcessor:

    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.frame_count = self.cap.get(int(cv2.CAP_PROP_FRAME_COUNT))

        self.index = 0

        # Record FPS
        self.total_time = 0
        self.previous_time = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cap.release()

    def release(self):
        self.cap.release()

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == self.frame_count:
            raise StopIteration
        
        if self.previous_time == 0:
            self.previous_time = time.time()

        self._ret, self._frame = self.cap.read()

        cur_time = time.time()
        self.total_time += (cur_time - self.previous_time)
        self.previous_time = cur_time

        if not self._ret:
            raise StopIteration

        self.index += 1
        return self._frame

    def __len__(self):
        return self.frame_count
    
    def get_fps(self):
        return self.index / self.total_time