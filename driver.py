from profiler import Profiler
from video_processor import VideoProcessor

def get_video_flow():
    sum_optical_flow = 0

    with VideoProcessor('videos/ny_driving.nut') as video:
        _ = next(video)
        prev_pred = video.predict()
        for frame in video:
            pred = video.predict()

            optical_flow = Profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            print(video.index, optical_flow)
            sum_optical_flow += optical_flow

            prev_pred = pred

        print(f'Video average flow: {sum_optical_flow / video.index}')
        return sum_optical_flow / video.index

def test_profiler():
    flow_method_one = get_video_flow()

    profiler = Profiler()
    with VideoProcessor('videos/ny_driving.nut') as video:
        for frame in video:
            profiler.add_frame(frame)
    
    flow_method_two = profiler.profile_buffer()

    assert flow_method_one == flow_method_two
    print('Flow Profiling Test Passing!')

if __name__ == '__main__':
    test_profiler()
    