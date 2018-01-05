import numpy as np
import scipy.ndimage
import cv2
from Trajectory import Trajectory


def bin_pixels(image, m=1, n=1):
    """
    Explicitly downsamples an image by an integer amount, by binning
    adjacent pixels m-by-n. Odd pixels on the bottom and right are
    discarded.
    """

    size = np.array(image.shape)
    size[0] = size[0] // m
    size[1] = size[1] // n
    new = np.zeros(size, dtype=image.dtype)
    for i in range(size[0]):
        for j in range(size[1]):
            tmp = np.mean(image[i * m: (i + 1) * m, j * n: (j + 1) * n], axis=(0, 1))
            if issubclass(image.dtype.type, np.integer):
                new[i, j] = np.round(tmp)
            else:
                new[i, j] = tmp
    return new


def filter_out_blobs(image, cutoff_area):
    """
    Takes an image and returns a version with only contiguous blobs
    with an area above cutoff_area left.
    """
    labeled_image, N = scipy.ndimage.label(image, structure=np.ones((3, 3)))
    # first, work out which is the biggest blob (except the background)
    output_image = np.zeros(image.shape, dtype=image.dtype)
    for i in range(1, N + 1):  # N doesn't include the background
        area = sum(sum(labeled_image == i))
        if area >= cutoff_area:
            output_image[np.where(labeled_image == i)] += 1
    output_image[np.where(output_image > .5)] = 1
    return output_image


def square(image):
    """
    Takes an image and returns a cropped, square version.
    """
    a = image
    dim = min(a.shape[:2])
    image = image[(a.shape[0]-dim)/2: (a.shape[0]-dim)/2+dim,
                  (a.shape[1]-dim)/2: (a.shape[1]-dim)/2+dim, ]
    return image


def pixels_to_trajectory(image):
        # TODO: play with the method parameter
        # different cv2 versions have different output here
        result = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        if len(result) == 2:
            contours, hierarchy = result
        elif len(result) == 3:
            null, contours, hierarchy = result
            del null

        # order the contours from top to bottom
        altitude = [np.max(c[:, 0, 1]) for c in contours]
        order = np.argsort(altitude)

        # package the curves in the standard way
        traces = Trajectory()
        for i in order:
            c = contours[i]
            c[:, 0, 1] = image.shape[0] - c[:, 0, 1]
            traces.append(c[:, 0, :])
        return traces
