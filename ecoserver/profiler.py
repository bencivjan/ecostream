import math
import numpy as np
import queue
from ultralytics import YOLO
import torch.cuda

class Profiler:
    def __init__(self, buffer_size=0):
        self.buffer = queue.Queue(maxsize=buffer_size)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO('yolov8l.pt').to(device)

    def profile_buffer(self):
        profile_size = self.buffer.qsize()
        optical_flow_sum = 0

        try:
            prev_frame = self.buffer.get_nowait()
        except queue.Empty:
            print('No frames in buffer to profile')
            return 0

        prev_pred = self.model.predict(prev_frame, verbose=False)

        for i in range(1, profile_size):
            try:
                frame = self.buffer.get_nowait()
            except queue.Empty:
                print('No frames in buffer to profile')
                break
            pred = self.model.predict(frame, verbose=False)

            optical_flow = Profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            optical_flow_sum += optical_flow
            
            prev_frame = frame
            prev_pred = pred
        
        return optical_flow_sum / profile_size if profile_size > 0 else 0

    def add_frame(self, frame):
        try:
            self.buffer.put_nowait(frame)
        except queue.Full:
            print('Queue is full, dropping oldest frame')
            self.buffer.get()
            self.buffer.put_nowait(frame)

    @staticmethod
    def get_center(box):
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return center_x, center_y

    @staticmethod
    def euclidean_distance(point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @staticmethod
    def calc_optical_flow(prev_prediction, prediction):
        # We need to associate previous objects with current objects
        # Use closest object of same class as the metric

        distance_matrix = np.full((len(prediction), len(prev_prediction)), float('inf'))

        for i, box in enumerate(prediction):
            for j, prev_box in enumerate(prev_prediction):
                if box.cls == prev_box.cls:
                    prev_center = Profiler.get_center(prev_box.xyxy[0])
                    curr_center = Profiler.get_center(box.xyxy[0])
                    distance_matrix[i, j] = Profiler.euclidean_distance(prev_center, curr_center)

        distance_matrix = distance_matrix.min(axis=1)
        distance_matrix[distance_matrix == float('inf')] = 0
        return distance_matrix.mean()

if __name__ == '__main__':
    # Test

    class Box():
        def __init__(self, cls, xyxy):
            self.cls = cls
            self.xyxy = xyxy

    box1 = Box(1, [[0, 0, 2, 2]])
    box2 = Box(1, [[2, 2, 4, 4]])
    
    box3 = Box(1, [[1, 0, 3, 2]])
    box4 = Box(1, [[4, 2, 6, 4]])

    average_distance = Profiler.calc_optical_flow([box1, box2], [box3, box4])
    print(f"Average distance moved: {average_distance}")
