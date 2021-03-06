import numpy as np
from . import utils
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
try:
    from skimage.morphology import skeletonize
    HAS_SKIM = True
except ImportError:
    HAS_SKIM = False
import time

from .Trajectory import Trajectory
from . import Filters


class Sketch(object):
    """
    Image handling class which loads and holds an image and creates
    drawing trajectories in various ways.
    """

    def __init__(self, image=None, max_size=None):
        """
        Constructor.

        image: Filename, function that returns an ndarray image, or just
               an ndarray.
        """
        if image is not None:
            self.read_image(image, max_size)

    def read_image(self, image, max_size=None):
        if not HAS_CV2:
            raise RuntimeError('OpenCV needed for this operation')
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
        if max_size is not None:
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

    def contour_drawing(self,
                        filter_list=[{"difference_of_gaussians": {
                               "larger_filter_size": 3,
                               "smaller_filter_size": 1,
                               "threshold": 3
                               }
                                    }],
                        min_blob_size=100,
                        smooth=False, **kwargs):
        """
        Makes a pencil drawing of the image, returned as a Trajectory.
        We find ridges by a difference-of-Gaussians filter

        filter_list: A list of filter descriptors.
            Each descriptor is a dict containing a single item.
            The key of the item indicates the name of the filter function.
            The value of the item is a dict of keywords passed to the filter function.

        min_blob_size: edges with an area below this value are filtered out

        smooth: Whether to smooth the drawing to lose pixel steps

        **kwargs: passed to scipy.signal.savgol_filter through Trajectory.smooth
        """
        if not HAS_SKIM:
            raise "skimage needed for this operation"

        image = self.image.astype(np.float64)

        mask = np.zeros(shape=image.shape, dtype=np.bool)
        for filter_descriptor in filter_list:
                for filter_name, filter_kwargs in filter_descriptor.iteritems():
                    filter_func = Filters.filter_lookup(filter_name)
                    filtered_image = filter_func(image, **filter_kwargs)
                    mask = np.logical_or(mask, filtered_image)

        blobbed = utils.filter_out_blobs(mask, min_blob_size)
        skeletonized = skeletonize(blobbed)
        skeletonized = skeletonized.astype('uint8')

        # translate edges to contour paths
        t0 = time.time(); print 'tracing...'
        traj = utils.pixels_to_trajectory(skeletonized)
        print '...%f' % (time.time() - t0)

        # smooth
        if smooth:
            print 'smoothing...'
            traj.smooth(**kwargs)

        return traj

    def multiple_shifted_lines_plot(self, n_lines, n_scans, gain=1,
                                    snake_scan=True):
        """
        Returns a Trajectory consisting of multiple overlapping line scans,
        for the current image with darkness modulated by the vertical offset
        between scans.
        """

        master_trajectory = Trajectory()
        for max_offset in np.linspace(-gain, gain, n_scans):
            scan_trajectory = self._shifted_lines_plot(n_lines=n_lines, max_offset=max_offset,
                                                       snake_scan=snake_scan)
            master_trajectory.paths += scan_trajectory.paths # Maybe implement Trajectory.__add__?
            # Todo: Add option to start every other iteration from the bottom
        return master_trajectory

    def _shifted_lines_plot(self, n_lines, max_offset=1, snake_scan=True):
        """
        Returns line scan Trajectory for the current image with darkness
        modulated as vertical offset.
        """

        linewidth = self.image.shape[0] / n_lines
        binnedImage = utils.bin_pixels(self.image, m=linewidth, n=1)
        lines = Trajectory()
        for line in range(n_lines):
            # j is the horizontal pixel index, one for each horizontal step
            j = np.arange(binnedImage.shape[1])
            # the darkness per stop of this particular line
            lineIntensity = (255.0 - binnedImage[line]) / 255.0
            # scale the waveform
            i = max_offset * lineIntensity * linewidth / 2.0
            # add the row offset
            i += (linewidth * line + linewidth / 2)
            # convert to cartesian coordinates
            xy = np.vstack((j, n_lines * linewidth - i)).T
            lines.append(xy)

        if snake_scan:
            self._make_snake_scan(lines)

        return lines

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
    except ImportError:
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
    traj = s.contour_drawing()
    traj.plot()

    plt.subplot(326)
    plt.imshow(s.image, cmap='gray')

    # Pencil sketch as a movie
    plt.figure()
    filter_list = [{"difference_of_gaussians": {
                   "larger_filter_size": 5,
                   "smaller_filter_size": 3,
                   "threshold": 5
                   }},
                   {"difference_of_gaussians": {
                    "larger_filter_size": 3,
                    "smaller_filter_size": 1,
                    "threshold": 5
                    }}
                   ]
    traj = s.contour_drawing(filter_list)
    traj.plot(movie=False, shape=s.image.shape)
