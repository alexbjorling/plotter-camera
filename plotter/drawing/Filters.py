try:
    import scipy.ndimage as ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def filter_lookup(filter_name):
    if filter_name == "difference_of_gaussians":
        return difference_of_gaussians
    else:
        print "No filter named", filter_name


def difference_of_gaussians(image, larger_filter_size=5, smaller_filter_size=3,
                            threshold=0):
        if not HAS_SCIPY:
            raise RuntimeError('This operation requires scipy.')
        image_small_filter = ndimage.filters.gaussian_filter(image, larger_filter_size)
        image_large_filter = ndimage.filters.gaussian_filter(image, smaller_filter_size)
        difference_image = image_small_filter - image_large_filter
        thresholded_image = difference_image > threshold
        return thresholded_image
