import multiprocessing
import os
import time

from datetime import datetime
from pytz import timezone

import cv2

"""
This module is designed to interface with Earthcam cameras and download
frames via multithreading and save them with their camera IDs and current date-time
"""

def _clean_cams():
    """
    Removes dead cameras from camera list
    """
    with open('deadCams.txt', 'r') as deadCamFile:
        deadCamList = deadCamFile.readlines()

    with open('m3u8sMaster.txt', 'r') as masterListFile:
        masterList = masterListFile.readlines()

    updatedCamList = []
    
    for cam in masterList:
        if cam not in deadCamList:
            updatedCamList.append(cam)

    with open('m3u8s.txt', 'w') as updatedCamFile:
        updatedCamFile.writelines(updatedCamList)


def _report_dead_cam(m3u8_target):
    """
    Writes dead camera links to file to be removed 
    """
    with open("deadCams.txt", "a") as deadFile:
        deadFile.write(m3u8_target)

def _get_formatted_est():
    """
    Gets the current Eastern time as a str, formatted 'M-D-Y_h-m-s'
    """
    est = timezone("US/Eastern")
    curr_time = datetime.now(est)

    time_format = "%m-%d-%Y_%H-%M-%S"

    return curr_time.strftime(time_format)

def _get_earthcam_id(m3u8_target):
    """
    Rips the camera ID from the m3u8 string.
    """
    prefix = "http://video3.earthcam.com/fecnetwork/"
    suffix = ".flv/playlist.m3u8"
    cam_id = m3u8_target[len(prefix):m3u8_target.index(suffix)]

    return cam_id


def download_stream_frames(m3u8_target, save_path, num_frames=1, save_img_type="png"):
    """
    Worker function that downloads a specified number of frames from a target stream.
    WORKS FOR EARTHCAM STREAMS ONLY.

    Args:

        m3u8_target: (str) The link to the target camera stream.

        save_path: (str) The save directory path for the frames (must end in /)

        num_frames: (int) Default 1. The desired number of frames to download from the camera.

        save_img_type: (str) Default 'png'. The target image save format.
    """

    cam = cv2.VideoCapture(m3u8_target)

    failure_cnt = 0  # The number of total frame grab failures
    is_got_one_successfully = False

    for _i in range(num_frames):
        is_success, frame = cam.read()
        filename = _get_earthcam_id(m3u8_target) + "--" + _get_formatted_est() + \
                        "." + save_img_type

        if is_success:
            save_target = save_path + filename
            cv2.imwrite(save_target, frame)
            is_got_one_successfully = True
        else:
            failure_cnt += 1
            print "FAILURE: " + filename + ", FAILED " + str(failure_cnt)

            if failure_cnt >= 5:
                if is_got_one_successfully: # Camera might work
                    print "||||||" + _get_earthcam_id(m3u8_target) + "||||||"
                else: # Camera dead
                    print "******" + _get_earthcam_id(m3u8_target) + "******"
                    _report_dead_cam(m3u8_target)
                break
    cam.release()

    return failure_cnt


def download_stream_time(m3u8_target, save_path, runtime_sec=5, save_img_type="png"):
    """
    Worker function that downloads a specified number of frames from a target stream.
    WORKS FOR EARTHCAM STREAMS ONLY.

    Args:

        m3u8_target: (str) The link to the target camera stream.

        save_path: (str) The save directory path for the frames (must end in /)

        runtime_sec: (int) Default 5. The desired number of seconds to run the downloader for.

        save_img_type: (str) Default 'png'. The target image save format.
    """
    cam = cv2.VideoCapture(m3u8_target)

    failure_cnt = 0  # The number of total frame grab failures
    is_got_one_successfully = False

    termination_time = time.time() + runtime_sec

    while time.time() < termination_time:
        is_success, frame = cam.read()
        filename = _get_earthcam_id(m3u8_target) + "--" + _get_formatted_est() + \
                        "." + save_img_type

        if is_success:
            save_target = save_path + filename
            cv2.imwrite(save_target, frame)
            is_got_one_successfully = True
        else:
            failure_cnt += 1
            print "FAILURE: " + filename + ", FAILED " + str(failure_cnt)

            if failure_cnt >= 5:
                if is_got_one_successfully: # Camera seems to work sometimes
                    print "||||||" + _get_earthcam_id(m3u8_target) + "||||||"
                else: # Camera dead
                    print "******" + _get_earthcam_id(m3u8_target) + "******"
                break
    cam.release()

    return failure_cnt

def get_single_batch(MAX_BAtCH_ALLOWED_TIME, FRAMES_PER_CAM_PER_BATCH):

    """
    Downloads frames from m3u8s.txt via multithreading
    One thread per camera
    """

    STREAM_DOWNLOADERS = []

    with open("m3u8s.txt") as stream_file:
        
            
        CURR_BATCH_START_TIME = time.time()

        # Create a directory for the current download batch if it doesn't already exist
        MASTER_SAVE_DIR = "./pics/Batch-" + _get_formatted_est() + "/"

        print "======STARTING BATCH======"

        for stream_link in stream_file:
            cam_save_dir = MASTER_SAVE_DIR + "Cam-" + _get_earthcam_id(stream_link) + "/"
            # Create a directory for the current cam download if it doesn't already exist
            if not os.path.exists(cam_save_dir):
                os.makedirs(cam_save_dir)
               
            p = multiprocessing.Process(target=download_stream_frames,
                                        args=(stream_link, cam_save_dir, FRAMES_PER_CAM_PER_BATCH))
            STREAM_DOWNLOADERS.append(p)
            p.start()

        # Every 5 seconds, check if it's time to start a new batch
        while STREAM_DOWNLOADERS is not False: # While not empty
            STREAM_DOWNLOADERS = [p for p in STREAM_DOWNLOADERS if p.is_alive()]
            # Terminate early if it takes too long to finish the batch
            if time.time() >= (CURR_BATCH_START_TIME + MAX_BATCH_ALLOWED_TIME):
                for p in STREAM_DOWNLOADERS:
                    p.terminate()
                    p.join()
                print "======Prematurely terminated batch======"
                break
            else:
                time.sleep(5)

if __name__ == "__main__":
    """
    Downloads frames from m3u8s.txt via multithreading
    One thread per camera
    """    
    EXPERIMENT_END_TIME = time.time() + 60 * 3 # Run for a full 1 hours
    MAX_BATCH_ALLOWED_TIME = 60 * 1 # 1 minutes per batch, max
    FRAMES_PER_CAM_PER_BATCH = 10

    while time.time() < EXPERIMENT_END_TIME:
        get_single_batch(MAX_BATCH_ALLOWED_TIME, FRAMES_PER_CAM_PER_BATCH)        
        
    _clean_cams()
    print "======EXPERIMENT DONE======"
