import numpy as np
import utils
import cv2
import scipy as sp
import scipy.ndimage
from skimage.morphology import skeletonize

from Trajectory import Trajectory


class Sketch(object):
    """
    Image handling class which loads and holds an image and creates
    drawing trajectories in various ways.
    """

    def __init__(self, image=None, max_size=300):
        """
        Constructor.

        image: Filename, function that returns an ndarray image, or just
               an ndarray.
        """
        if image is not None:
            self.read_image(image, max_size)

    def read_image(self, image, max_size):
        if type(image) == str:
            self.image = cv2.cvtColor(
                cv2.imread(image, cv2.IMREAD_UNCHANGED),
                cv2.COLOR_BGR2RGB)
        elif type(image) == np.ndarray:
            self.image = image
        elif hasattr(image, '__call__'):
            self.image = image()

        # make sure image is grayscale
        while len(self.image.shape) > 2:
            self.image = np.mean(self.image, axis=-1)

        # make sure image is 8 bit
        self.image = self.image.astype(np.uint8)

        # resize image
        scale = float(max_size) / np.max(self.image.shape)
        self.image = cv2.resize(self.image, (0, 0), fx=scale, fy=scale)

    def amplitude_mod_scan(self, n_lines, pixels_per_period, gain=1,
                           waveform='square', snake_scan=True):
        """
        Returns line scan Trajectory for the current image with darkness
        modulated as amtlitude.
        """
        assert waveform in ['square', 'sawtooth']
        try:
            assert pixels_per_period % 2 == 0
            pixels_per_half_period = pixels_per_period / 2
        except AssertionError:
            raise ValueError('pixelsPerPerdiod must be even')

        linewidth = self.image.shape[0] / n_lines
        binnedImage = utils.bin_pixels(self.image, m=linewidth, n=pixels_per_half_period)
        lines = Trajectory()
        for line in range(n_lines):
            # j is the horizontal pixel index, one for each horizontal step
            j = np.arange(binnedImage.shape[1]) * pixels_per_half_period
            # the darkness per stop of this particular line
            lineIntensity = (255.0 - binnedImage[line]) / 255.0
            # basic sawtooth waveform
            i = np.arange(binnedImage.shape[1], dtype=float)
            i = (i % 2) * 2 - 1
            # scale the waveform
            i *= gain * lineIntensity * linewidth / 2.0
            # add the row offset
            i += (linewidth * line + linewidth / 2)
            # convert to cartesian coordinates
            xy = np.vstack((j, n_lines * linewidth - i)).T
            lines.append(xy)

        if waveform == 'square':
            # for each line, convert the sawtooth to a square by adding points
            # there's an extra zero somewhere but it works.
            for i in range(lines.number):
                x = lines[i][:, 0]
                y = lines[i][:, 1]
                xx = np.zeros(x.size * 2)
                yy = np.zeros(y.size * 2)
                xx[0::2] = x
                xx[1::2] = x
                yy[0::2] = y
                yy[1:-1:2] = y[1:]
                lines[i] = np.vstack((xx, yy)).T

        if snake_scan:
            self._make_snake_scan(lines)

        return lines

    def frequency_mod_scan(self, n_lines, pixels_per_typical_period, gain=1,
                           waveform='square', snake_scan=True):
        """
        Returns line scan Trajectory for the current image with darkness
        modulated as frequency.

        pixels_per_typical_period: the frequency at image value 255 / 2.0
        """
        assert waveform in ['square', 'sawtooth']
        linewidth = self.image.shape[0] / n_lines
        binnedImage = utils.bin_pixels(self.image, m=linewidth, n=1)

        lines = Trajectory()
        for line in range(n_lines):
            # the average darkness per pixel column of this particular line
            lineIntensity = (255.0 - binnedImage[line]) / 255.0
            # accumulated pixel intensity where the waveform changes value
            accThreshold = 1.0 / 2 * pixels_per_typical_period
            # now run through the row and flip the waveform when appropriate
            i, j = [-1, ], [0, ]
            acc = lineIntensity[0]
            for ii in range(1, len(lineIntensity)):
                acc += lineIntensity[ii]
                if acc > accThreshold:
                    if waveform == 'square':
                        j += [ii, ii]
                        i += [i[-1], -1*i[-1]]
                    elif waveform == 'sawtooth':
                        j += [ii]
                        i += [-1*i[-1]]
                    acc = 0
            j = np.array(j, dtype=float)
            i = np.array(i, dtype=float)
            # scale the waveform
            i *= gain * linewidth / 2.0
            # add the row offset
            i += (linewidth * line + linewidth / 2)
            # convert to cartesian coordinates
            xy = np.vstack((j, n_lines * linewidth - i)).T
            lines.append(xy)

        if snake_scan:
            self._make_snake_scan(lines)

        return lines

    def contour_drawing(self, larger_filter_size=5, smaller_filter_size=3,
                        threshold=-3, min_blob_size=100):
        """
        Makes a pencil drawing of the image, returned as a Trajectory.
        We find ridges by a difference-of-Gaussians filter

        smaller_filter_size: size of the small Gaussian filter
        larger_filter_size: size of the large Gaussian filter
        threshold: the cutoff for what constitutes a ridge

        min_blob_size: edges with an area below this value are filtered out
        """

        # Canny filter
        image = self.image.astype(np.float64)
        image_small_filter = sp.ndimage.filters.gaussian_filter(image, larger_filter_size)
        image_large_filter = sp.ndimage.filters.gaussian_filter(image, smaller_filter_size)
        difference_image = image_large_filter - image_small_filter
        # remove the smallest edges
        thresholded_image = difference_image < threshold
        thresholded_image = thresholded_image.astype(np.int64)
        blobbed = utils.filter_out_blobs(thresholded_image, min_blob_size)
        skeletonized = skeletonize(blobbed)
        skeletonized = skeletonized.astype('uint8')

        # translate edges to contour paths
        # TODO: play with the method parameter
        # different cv2 versions have different output here
        traj = utils.pixels_to_trajectory(skeletonized)
        return traj

    def _make_snake_scan(self, traj):
        """
        Make a raster scan a snake scan in-place.
        """
        for i in range(len(traj)):
            if i % 2:
                # revert odd lines
                traj[i] = np.flipud(traj[i])


# example usage
if __name__ == '__main__':

    try:
        import matplotlib.pyplot as plt
    except:
        exit(-1)

    plt.ion()
    s = Sketch('image.jpg', max_size=800)
    # from scipy.misc import ascent
    # s = Sketch(ascent)

    # Simple line scans with different types of modulation
    plt.figure(figsize=(14, 14))
    plt.subplot(321)
    traj = s.amplitude_mod_scan(n_lines=50, pixels_per_period=4, gain=1.3, waveform='square')
    traj.plot()

    plt.subplot(322)
    traj = s.amplitude_mod_scan(n_lines=50, pixels_per_period=4, gain=1.3, waveform='sawtooth')
    traj.plot()

    plt.subplot(323)
    traj = s.frequency_mod_scan(n_lines=50, pixels_per_typical_period=2.1, waveform='square')
    traj.plot()

    plt.subplot(324)
    traj = s.frequency_mod_scan(n_lines=50, pixels_per_typical_period=2.1, waveform='sawtooth')
    traj.plot()

    plt.subplot(325)
    traj = s.contour_drawing(larger_filter_size=3, smaller_filter_size=1)
    traj.plot()

    plt.subplot(326)
    plt.imshow(s.image, cmap='gray')

    # Pencil sketch as a movie
    plt.figure()
    traj = s.contour_drawing()
    traj.plot(movie=False, shape=s.image.shape)
