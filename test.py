import unittest
from profiler import Profiler
from video_processor import VideoProcessor
from ultralytics import YOLO
import torch.cuda

def get_video_flow():
    sum_optical_flow = 0

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO('yolov8l.pt').to(device)

    with VideoProcessor('videos/ny_driving.mov') as video:
        frame = next(video)
        prev_pred = model.predict(frame, verbose=False)
        for frame in video:
            pred = model.predict(frame, verbose=False)

            optical_flow = Profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            print(video.index, optical_flow)
            sum_optical_flow += optical_flow

            prev_pred = pred

        average_flow = sum_optical_flow / video.index
        print(f'Video average flow: {average_flow}')
        return average_flow

class TestProfiler(unittest.TestCase):

    def test_profiler(self):
        flow_method_one = get_video_flow()

        profiler = Profiler()
        with VideoProcessor('videos/ny_driving.mov') as video:
            for frame in video:
                profiler.add_frame(frame)
        
        flow_method_two = profiler.profile_buffer()

        self.assertEqual(flow_method_one, flow_method_two, msg="Flow profiling methods should produce the same result")
        print('Flow Profiling Test Passing!')

if __name__ == '__main__':
    unittest.main()
