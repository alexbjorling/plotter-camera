import matplotlib.pyplot as plt
import numpy as np
import utils
import cv2
from Trajectory import Trajectory


class Sketch(object):
    """
    Image handling class which loads and holds an image and creates 
    drawing trajectories in various ways.
    """

    def __init__(self, image=None):
        """
        Constructor.

        image: Filename, function that returns an ndarray image, or just 
               an ndarray.
        """
        if image is not None:
            self.read_image(image)

    def read_image(self, image, max_size=320):
        if image == str(image):
            self.image = plt.imread(image)
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

    def amplitudeModScan(self, nLines, pixelsPerPeriod, gain=1, waveform='square'):
        """ 
        Returns line scan Trajectory for the current image with darkness
        modulated as amtlitude.
        """
        assert waveform in ['square', 'sawtooth']
        try:
            assert pixelsPerPeriod % 2 == 0
            pixelsPerHalfPeriod = pixelsPerPeriod / 2
        except AssertionError:
            raise ValueError('pixelsPerPerdiod must be even')

        linewidth = self.image.shape[0] / nLines
        binnedImage = utils.binPixels(self.image, m=linewidth, n=pixelsPerHalfPeriod)
        lines = Trajectory()
        for line in range(nLines):
            # j is the horizontal pixel index, one for each horizontal step
            j = np.arange(binnedImage.shape[1]) * pixelsPerHalfPeriod
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
            xy = np.vstack((j, nLines * linewidth - i)).T
            lines.append(xy)

        if waveform == 'square':
            # for each line, convert the sawtooth to a square by adding points
            # there's an extra zero somewhere but it works.
            for i in range(lines.number):
                x = lines[i][:,0]
                y = lines[i][:,1]
                xx = np.zeros(x.size * 2)
                yy = np.zeros(y.size * 2)
                xx[0::2] = x
                xx[1::2] = x
                yy[0::2] = y
                yy[1:-1:2] = y[1:]
                lines[i] = np.vstack((xx, yy)).T

        return lines

    def frequencyModScan(self, nLines, pixelsPerTypicalPeriod, gain=1, waveform='square'):
        """ 
        Returns line scan Trajectory for the current image with darkness
        modulated as frequency.

        pixelsPerTypicalPeriod: the frequency at image value 255 / 2.0
        """
        assert waveform in ['square', 'sawtooth']
        linewidth = self.image.shape[0] / nLines
        binnedImage = utils.binPixels(self.image, m=linewidth, n=1)

        lines = Trajectory()
        for line in range(nLines):
            # the average darkness per pixel column of this particular line
            lineIntensity = (255.0 - binnedImage[line]) / 255.0
            # accumulated pixel intensity where the waveform changes value
            accThreshold = 1.0 / 2 * pixelsPerTypicalPeriod
            # now run through the row and flip the waveform when appropriate
            i, j = [-1,], [0,]
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
            xy = np.vstack((j, nLines * linewidth - i)).T
            lines.append(xy)
        return lines

    def contourDrawing(self, cutoff=80, minBlobSize=20):
        """
        Makes a pencil drawing of the image, returned as a Trajectory.

        cutoff: the lower Canny filter cutoff
        minBlobSize: edges with an area below this value are filtered out
        """

        # Canny filter
        lower = cutoff
        upper = 3 * lower
        edges = cv2.Canny(self.image, lower, upper, apertureSize=3) / 255

        # remove the smallest edges
        blobbed = utils.filterOutBlobs(edges, minBlobSize)

        # TODO: make sure there are no thick lines! this messes up the contours

        # translate edges to contour paths
        # TODO: play with the method parameter
        contours, hierarchy = cv2.findContours(blobbed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        # order the contours from top to bottom
        altitude = [np.max(c[:,0,1]) for c in contours]
        order = np.argsort(altitude)

        # package the curves in the standard way
        traces = Trajectory()
        for i in order:
            c = contours[i]
            c[:,0,1] = self.image.shape[0] - c[:,0,1]
            traces.append(c[:,0,:])
        return traces


# example usage
if __name__ == '__main__':
    plt.ion()
    s = Sketch('image.jpg')
    #from scipy.misc import ascent
    #s = Sketch(ascent)
    
    # Simple line scans with different types of modulation
    plt.figure(figsize=(14,14))
    plt.subplot(321)
    traj = s.amplitudeModScan(nLines=50, pixelsPerPeriod=4, gain=1.3, waveform='square')
    traj.plot()
    
    plt.subplot(322)
    traj = s.amplitudeModScan(nLines=50, pixelsPerPeriod=4, gain=1.3, waveform='sawtooth')
    traj.plot()
    
    plt.subplot(323)
    traj = s.frequencyModScan(nLines=50, pixelsPerTypicalPeriod=2.1, waveform='square')
    traj.plot()
    
    plt.subplot(324)
    traj = s.frequencyModScan(nLines=50, pixelsPerTypicalPeriod=2.1, waveform='sawtooth')
    traj.plot()

    plt.subplot(325)
    traj = s.contourDrawing()
    traj.plot()

    plt.subplot(326)
    plt.imshow(s.image, cmap='gray')

    # Pencil sketch as a movie
    plt.figure()
    traj = s.contourDrawing()
    traj.plot(movie=True, shape=s.image.shape)
