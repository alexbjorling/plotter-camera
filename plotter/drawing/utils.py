import numpy as np
import scipy.ndimage

def binPixels(image, m=1, n=1):
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
            tmp = np.mean(image[i * m : (i + 1) * m, j * n : (j + 1) * n], axis=(0, 1))
            if issubclass(image.dtype.type, np.integer):
                new[i, j] = np.round(tmp)
            else:
                new[i, j] = tmp
    return new

def filterOutBlobs(image, cutoffArea):
    """ 
    Takes an image and returns a version with only contiguous blobs
    with an area above cutoffArea left.
    """
    labeledImage, N = scipy.ndimage.label(image, structure=np.ones((3,3)))
    # first, work out which is the biggest blob (except the background)
    outputImage = np.zeros(image.shape, dtype=image.dtype)
    for i in range(1, N + 1): # N doesn't include the background
        area = sum(sum(labeledImage == i))
        if area >= cutoffArea:
            outputImage[np.where(labeledImage == i)] += 1
    outputImage[np.where(outputImage > .5)] = 1
    return outputImage

def square(image):
    """
    Takes an image and returns a cropped, square version.
    """
    a = image
    dim = min(a.shape[:2])
    image = image[(a.shape[0]-dim)/2 : (a.shape[0]-dim)/2+dim,
                  (a.shape[1]-dim)/2 : (a.shape[1]-dim)/2+dim,]
    print image.shape
    return image
