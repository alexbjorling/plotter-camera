import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt

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

def plotSketch(scan, movie=False, shape=None, **kwargs):
    """
    Plot a sketch consisting of a list of (x, y) arrays.

    move: plot point by point
    shape: shape of final image, (y x)
    kwargs: passed to plt.plot
    """
    # default plot settings
    if (not 'color' in kwargs.keys()) and (not 'c' in kwargs.keys()):
        kwargs['color'] = 'k'
    if (not 'linestyle' in kwargs.keys()) and (not 'ls' in kwargs.keys()):
        kwargs['linestyle'] = '-'

    ax = plt.gca()
    if shape:
        ax.set_ylim([0, shape[0]])
        ax.set_xlim([0, shape[1]])
    for line in range(len(scan)):
        if movie:
            # trace out each curve point by point
            for t in scan:
                for ii in range(2, t.shape[0]):
                    plt.plot(t[ii-2:ii,0], t[ii-2:ii,1], **kwargs)
                    plt.pause(.001)
        else:
            # just plot each curve in its entirety
            plt.plot(scan[line][:,0], scan[line][:,1], **kwargs)
    ax.set_aspect('equal')
    plt.autoscale(tight=True)