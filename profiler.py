import math
import numpy as np
from queue import Queue
from ultralytics import YOLO
import torch.cuda

class Profiler:
    def __init__(self, buffer_size=0):
        self.buffer = Queue()
        self.buffer_size = buffer_size

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO('yolov8l.pt').to(device)

    def profile_buffer(self):
        profile_size = self.buffer_size if self.buffer_size > 0 else self.buffer.qsize()
        optical_flow_sum = 0

        prev_frame = self.buffer.get()
        prev_pred = self.model.predict(prev_frame, verbose=False)

        for i in range(profile_size-1):
            frame = self.buffer.get()
            pred = self.model.predict(prev_frame, verbose=False)

            optical_flow = Profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            print(optical_flow)
            optical_flow_sum += optical_flow
            
            prev_frame = frame
            prev_pred = pred
            frame = self.buffer.get()
            print(i)
        
        return optical_flow_sum / self.buffer_size

    def add_frame(self, frame):
        self.buffer.put(frame)

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

    @staticmethod
    def calculate_iou(box1, box2):
        """
        Calculate the Intersection over Union (IoU) of two bounding boxes.

        Parameters:
        - box1, box2: Lists or tuples with 4 elements each [x, y, width, height].

        Returns:
        - IoU: Intersection over Union (float).
        """
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        inter_min_x = max(x1_min, x2_min)
        inter_min_y = max(y1_min, y2_min)
        inter_max_x = min(x1_max, x2_max)
        inter_max_y = min(y1_max, y2_max)

        inter_width = max(0, inter_max_x - inter_min_x)
        inter_height = max(0, inter_max_y - inter_min_y)

        inter_area = inter_width * inter_height
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)

        union_area = box1_area + box2_area - inter_area

        iou = inter_area / union_area if union_area != 0 else 0

        return iou

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
