import sys, os
mod_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if mod_dir not in sys.path:
    sys.path.append(mod_dir)

import time
import cv2
import ecostream
from ecoclient.video_processor import VideoProcessor
from ecoclient.utils import throttle
from ffenc_uiuc.ffenc import ffenc
from ffenc_uiuc.ffdec import ffdec

current_frame = None

def generate_ground_truth():
    global current_frame

    with VideoProcessor('../videos/crosswalk.avi') as video:
        encoder = ffenc(int(video.width), int(video.height), int(video.fps))
        decoder = ffdec()
        for frame in video:
            start_time = time.time()
            out = encoder.process_frame(frame)
            current_frame = decoder.process_frame(out)
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(f'ground-truth/frame_{video._index}.jpg', current_frame)
            if not throttle(target_fps=30, start_time=start_time):
                print('No throttle')
            print(video._index)

def main():
    os.makedirs('ground-truth', exist_ok=True)
    os.makedirs('ecostream', exist_ok=True)
    generate_ground_truth()

if __name__ == '__main__':
    main()