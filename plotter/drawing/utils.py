import numpy as np

try:
    import skimage
    HAS_SKIM = True
except ImportError:
    HAS_SKIM = False

from .Trajectory import Trajectory


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
    if not HAS_SKIM:
        raise RuntimeError('This operation requires skimage.')
    skimage.morphology.remove_small_objects(image, min_size=cutoff_area, connectivity=2, in_place=True)
    return image


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

    def walk(image, start, max_steps):
        """
        Generator which walks along positive pixels and yields the indices passed.
        Returns when the end of the line is reached or after max_steps.
        """
        i, j = start
        mask = np.empty((3,3), dtype=np.uint8)
        for step in range(max_steps):
            yield i, j
            mask[:] = 1
            mask[1, 1] = 0
            if step:
                mask[last_pos] = 0
            masked = mask * image[i-1:i+2, j-1:j+2]
            if not masked.max():
                return
            direction = np.array(np.unravel_index(np.argmax(masked), (3,3))) - 1
            last_pos = tuple(1 - direction)
            i += direction[0]
            j += direction[1]

    # cheat the boundaries
    image[0,:] = 0
    image[-1, :] = 0
    image[:, -1] = 0
    image[:, 0] = 0

    traj = Trajectory()
    while image.max():
        # pick an arbitrary positive pixel
        i, j = np.unravel_index(np.argmax(image), image.shape)

        # try finding the end of the line, max N pixels
        for ind in walk(image, (i, j), 1000):
            pass

        # walk again
        t = []
        for ind in walk(image, ind, 1000):
            t.append(ind)
            image[ind] = 0

        arr = np.fliplr(np.array(t))
        arr[:, 1] = image.shape[0] - arr[:, 1]
        traj.append(arr)
    return traj
