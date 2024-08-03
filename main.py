import profiler
from video_processor import VideoProcessor

def main():
    sum_optical_flow = 0

    with VideoProcessor('videos/ny_driving.mov') as video:
        _ = next(video)
        prev_pred = video.predict()
        for frame in video:
            pred = video.predict()

            optical_flow = profiler.calc_optical_flow(prev_pred[0].boxes, pred[0].boxes)
            print(video.index, optical_flow)
            sum_optical_flow += optical_flow

            prev_pred = pred

        print(f'Video average flow: {sum_optical_flow / video.index}')

if __name__ == '__main__':
    main()
    