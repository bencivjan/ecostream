import sys, os
mod_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

import time
import argparse
import cv2
from ecoclient.video_processor import VideoProcessor
from ecoclient.utils import throttle
from ecoclient.client import EcoClient
from ffenc_uiuc.h264_encoder import ffenc, ffdec

GROUND_TRUTH_DIR = 'ground-truth-output'
ECOSTREAM_DIR = '30fps'

def generate_frames(video_path: str, ecoclient: EcoClient):
    total_start_time = time.time()
    with VideoProcessor(video_path) as video:
        encoder = ffenc(int(video.width), int(video.height), int(video.fps))
        decoder = ffdec()
        current_frame = None
        for frame in video:
            start_time = time.time()
            # out = encoder.process_frame(frame)
            # current_frame = decoder.process_frame(out)
            # current_frame = cv2.cvtColor(current_frame, cv2.COLOR_RGB2BGR)
            # cv2.imwrite(os.path.join(os.path.dirname(__file__), 'ground-truth-output', f'frame_{video._index}.jpg'), frame)
            ecoclient.set_eval_params(frame,
                                      os.path.join(os.path.dirname(__file__), ECOSTREAM_DIR, f'frame_{video._index}.jpg'))
            throttle(target_fps=30, start_time=start_time)

            print(video._index)
            # Start eval once we have set the eval params
            if video._index == 1:
                ecoclient.start_eval()

        ecoclient.set_eval_params(None, None)
        print(f'Ground truth fps: {EcoClient.get_fps(total_start_time, time.time(), video._index)}')

def generate_frames_at_fps(video_path: str, fps: int):
    # Calculate the time to wait between frames
    frame_time = 1.0 / fps

    total_start_time = time.time()
    # Read save frame at predetermined fps
    with VideoProcessor(video_path) as video:
        for frame in video:
            start_time = time.time()

            throttle(target_fps=30, start_time=start_time)

            elapsed_time = time.time() - total_start_time
            if elapsed_time > frame_time: # We have waited long enough to save
                print('Saving frame')
                cv2.imwrite(os.path.join(os.path.dirname(__file__), ECOSTREAM_DIR, f'frame_{video._index}.jpg'), frame)
                total_start_time = time.time()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server_ip', type=str, default='localhost')
    parser.add_argument('-p', '--server_port', type=int, default=8010)
    args = parser.parse_args()

    os.makedirs(os.path.join(os.path.dirname(__file__), GROUND_TRUTH_DIR), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), ECOSTREAM_DIR), exist_ok=True)
    # ecoclient = EcoClient(None, args.server_ip, args.server_port)
    # generate_frames('../videos/crosswalk.mp4', ecoclient)

    generate_frames_at_fps('../videos/ny_driving.mov', 35)

if __name__ == '__main__':
    main()