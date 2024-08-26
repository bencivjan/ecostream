import sys, os
mod_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

import unittest
from ecoserver.profiler import Profiler
from ecoclient.video_processor import VideoProcessor
from ultralytics import YOLO
import torch.cuda

def get_video_flow(path):
    sum_optical_flow = 0

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO(os.path.join(PATH_STEM, '..', 'yolov8x.pt')).to(device)

    with VideoProcessor(path) as video:
        frame = next(video)
        prev_pred = model.predict(frame, verbose=False)
        for frame in video:
            pred = model.predict(frame, verbose=False)

            optical_flow = Profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            print(video._index, optical_flow)
            sum_optical_flow += optical_flow

            prev_pred = pred

        average_flow = sum_optical_flow / video._index
        return average_flow
    
def get_video_flow_profiler(path):
    profiler = Profiler()

    with VideoProcessor(path) as video:
        for frame in video:
            profiler.add_frame(frame)
            print(video._index)
        
    return profiler.profile_buffer()

def calc_avg_box_size(bboxes):
    if bboxes.size == 0:
        return 0.0
    
    total_area = 0
    for bbox in bboxes:
        x_min, y_min, x_max, y_max = bbox
        width = x_max - x_min
        height = y_max - y_min
        area = width * height
        total_area += area
    
    average_area = total_area / len(bboxes)
    return average_area

def get_video_obj_size(path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO(os.path.join(PATH_STEM, '..', 'yolov8x.pt')).to(device)

    average_size = 0
    
    with VideoProcessor(path) as video:
        for frame in video:
            print(f'Frame {video._index}')
            pred = model.predict(frame, verbose=False)
            size = calc_avg_box_size(pred[0].boxes.xyxy)
            average_size += size
            print(f'Avg size: {size}')
    
    return average_size / video._index

class TestProfiler(unittest.TestCase):

    def test_profiler(self):
        flow_method_one = get_video_flow('videos/ny_driving.mov')

        flow_method_two = get_video_flow_profiler('videos/ny_driving.mov')

        print(f'{flow_method_one}, {flow_method_two}')
        self.assertEqual(flow_method_one, flow_method_two, msg="Flow profiling methods should produce the same result")
        print('Flow Profiling Test Passing!')

if __name__ == '__main__':
    PATH_STEM = os.path.dirname(__file__)
    
    # unittest.main()
    # print(f'Video average flow: {round(get_video_flow('../videos/ny_driving.mov'), 4)}')

    # print(f'Video average obj size: {get_video_obj_size('../videos/crosswalk.mp4')}')
    print(f'Video average obj size: {get_video_obj_size('../videos/ny_driving.mov')}')
