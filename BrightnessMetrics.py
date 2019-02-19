import os
import numpy as np
import pickle
import cv2



"""
Main program header
include programmers, project github, instructions how to use etc
"""

"""
Do we have a cv2 img?
"""
def is_valid_img(img):
    if not isinstance(img, np.ndarray):
        print("Error: cv2 image not passed!")
        return False
    else:
        return True

"""
Perceived Brightness = Sqrt((0.241 * R^2) + (0.691 * G^2) + (0.068 * B^2)) 
"""
def calc_perceived_brightness(img):
    height, width, dim = img.shape
    return ( np.sqrt(((np.sum(img[:, :, 2]) ** 2) * 0.241) + ((np.sum(img[:, :, 1]) ** 2) * 0.691) + ((np.sum(img[:, :, 0]) ** 2) * 0.068)) / (height * width * 255))


"""
Luminance
Luminance = (0.299 * R) + (0.578 * G) + (0.114 * B)
"""
def calc_luminosity(img):
    height, width, dim = img.shape
    return (np.sum(img[:, :, 2]) * 0.299 + np.sum(img[:, :, 1]) * 0.578 + np.sum(img[:, :, 0]) * 0.114) / (height * width * 255)

"""
Pixel Intensity
1.Converts image to greyscale
2. Takes the average pixel value
"""
def calc_px_intensity(img):
    gImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width= gImg.shape
    return np.sum(gImg) / (height * width * 255)

"""
Runs analysis on a single image and 
"""
def run_single_analysis(working_path, fileLoc, data):
    img = cv2.imread(fileLoc)
    if is_valid_img(img):
        lum = calc_luminosity(img)
        px_int = calc_px_intensity(img)
        percB = calc_perceived_brightness(img)
        data.append([fileLoc.replace(working_path, "."), lum, px_int, percB])
    else:
        print("ERROR: Invalid Image: " + fileLoc)



"""
Goes through all .jpg or .png images in specified directory and all subdirectories
"""
def run_mass_analysis():

    orig_path = os.path.realpath(".")
    while True:
        working_path = raw_input("Input path (relative or absolute) to directory to be evaluated\n Relative paths should start with './' \n Absolute paths should start with or '/' \nEnter Path: ")
        try:
            os.chdir(working_path)
        except:
            print("ERROR: Invalid directory")
        else:
            break

    working_path = os.path.realpath(".")
    data = [["Absolute Path: ", working_path],[]]
    data.append(["Image_Location", "Luminosity", "Pixel_Intensity", "Perceived_Brightness"])

    for subDir, dirs, files in os.walk(working_path):
        for file in files:
            fileLoc = os.path.join(subDir,file)
            if (".jpg" in fileLoc) or (".png" in fileLoc):
                run_single_analysis(working_path, fileLoc, data)
    with open('brightnessResults.pkl', 'wb') as fp:
        pickle.dump(data, fp)
    print(data)
    os.chdir(orig_path)

if __name__ == "__main__":
    run_mass_analysis()
    pass