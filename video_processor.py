import cv2
from ultralytics import YOLO
import torch.cuda

class VideoProcessor:

    def __init__(self, video_path, requested_fps=None):
        self.cap = cv2.VideoCapture(video_path)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO('yolov8l.pt').to(device)

        self.frame_count = self.cap.get(int(cv2.CAP_PROP_FRAME_COUNT))
        self.real_fps = self.cap.get(int(cv2.CAP_PROP_FPS))

        if requested_fps:
            self.requested_fps = requested_fps
        else:
            self.requested_fps = self.real_fps

        if self.real_fps > self.requested_fps:
            raise ValueError(f'Requested fps {requested_fps} must be larger than real fps {self.real_fps}')

        self.index = 0

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
        
        # Only read new image from video if the frame index is divisible by the real : requested fps ratio
        # E.g. requested_fps = 30, real_fps = 10. We want to read a new real video frame every 3 requested frames,
        #       otherwise we return the last read frame to avoid running out of frames early.
        #       We will reuse the same predictions for these intermediate frames.

        # if self.index % (self.real_fps // self.requested_fps) == 0:
        self._ret, self._frame = self.cap.read()

        if not self._ret:
            raise StopIteration

        self.index += 1
        return self._frame

    def __len__(self):
        return self.frame_count