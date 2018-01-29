import multiprocessing

from datetime import datetime
from pytz import timezone

import cv2

"""
This module is designed to interface with Earthcam cameras and download
frames via multithreading and save them with their camera IDs and current date-time
"""


def _get_formatted_est():
    """
    Gets the current Eastern time as a str, formatted 'M-D-Y.h_m_s'
    """
    est = timezone("US/Eastern")
    curr_time = datetime.now(est)

    time_format = "%m-%d-%Y.%H_%M_%S"

    return curr_time.strftime(time_format)


def download_stream(m3u8_target, save_path, num_frames=1, save_img_type="png"):
    """
    Worker function that downloads a specified number of frames from a target stream.
    WORKS FOR EARTHCAM STREAMS ONLY.

    Args:

        m3u8_target: (str) The link to the target camera stream.

        save_path: (str) The save directory path for the frames (must end in /)

        num_frames: (int) Default 1. The desired number of frames to download from the camera.

        save_img_type: (str) Default 'png'. The target image save format.
    """
    prefix = "http://video3.earthcam.com/fecnetwork/"
    suffix = ".flv/playlist.m3u8"

    cam = cv2.VideoCapture(m3u8_target)

    failure_cnt = 0  # The number of total frame grab failures

    for _i in range(num_frames):
        is_success, frame = cam.read()
        if is_success:
            cam_id = m3u8_target[len(prefix):m3u8_target.index(suffix)]
            filename = cam_id + "--" + _get_formatted_est() + "." + save_img_type
            filename = save_path + filename
            print filename
            cv2.imwrite(filename, frame)
        else:
            failure_cnt += 1
    cam.release()

    return failure_cnt


if __name__ == "__main__":
    """
    Downloads frames from m3u8s.txt via multithreading
    One thread per camera
    """

    STREAM_DOWNLOADERS = []

    with open("m3u8s.txt") as stream_file:
        for stream_link in stream_file:
            p = multiprocessing.Process(target=download_stream,
                                        args=(stream_link, "./allCollectedImages/"))
            STREAM_DOWNLOADERS.append(p)
            p.start()
