import sys, os
mod_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

import time
import cv2
import threading
from ecoclient.video_processor import VideoProcessor
from ecoclient.utils import throttle
from ecoclient.client import EcoClient
from ffenc_uiuc.h264_encoder import ffenc, ffdec

GROUND_TRUTH_DIR = 'ground-truth-output'
ECOSTREAM_DIR = 'ecostream-output'

def generate_frames(ecoclient: EcoClient):
    video_path = os.path.join(os.path.dirname(__file__), '..', 'videos', 'crosswalk.avi')
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

def main():
    os.makedirs(os.path.join(os.path.dirname(__file__), GROUND_TRUTH_DIR), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), ECOSTREAM_DIR), exist_ok=True)
    ecoclient = EcoClient(None, '192.168.130.140', 8010)
    generate_frames(ecoclient)

if __name__ == '__main__':
    main()