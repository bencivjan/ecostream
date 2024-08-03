import math
import numpy as np

def get_center(box):
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y

def euclidean_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def calc_optical_flow(prev_prediction, prediction):
    # We need to associate previous objects with current objects
    # Use closest object of same class as the metric

    distance_matrix = np.full((len(prediction), len(prev_prediction)), float('inf'))

    for i, box in enumerate(prediction):
        for j, prev_box in enumerate(prev_prediction):
            if box.cls == prev_box.cls:
                prev_center = get_center(prev_box.xyxy[0])
                curr_center = get_center(box.xyxy[0])
                distance_matrix[i, j] = euclidean_distance(prev_center, curr_center)

    distance_matrix = distance_matrix.min(axis=1)
    distance_matrix[distance_matrix == float('inf')] = 0
    return distance_matrix.mean()

    
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

    average_distance = calc_optical_flow([box1, box2], [box3, box4])
    print(f"Average distance moved: {average_distance}")
