import matplotlib.pyplot as plt
import numpy as np
import utils
import cv2

# TODO: util which calculates the total travel path of a a sketch for comparison

class Sketch(object):

    def __init__(self, imfile):
        self.image = plt.imread(imfile)
        self.bwimage = np.mean(self.image, axis=-1)

    def amplitudeModScan(self, nLines, pixelsPerPeriod, gain=1, waveform='square'):
        """ 
        Returns line scan trajectory for the current image, as list of 
        (x, y) arrays, with darkness modulated as amtlitude.
        """
        assert waveform in ['square', 'sawtooth']
        try:
            assert pixelsPerPeriod % 2 == 0
            pixelsPerHalfPeriod = pixelsPerPeriod / 2
        except AssertionError:
            raise ValueError('pixelsPerPerdiod must be even')

        linewidth = self.image.shape[0] / nLines
        binnedImage = utils.binPixels(self.bwimage, m=linewidth, n=pixelsPerHalfPeriod)
        lines = []
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
            for i in range(len(lines)):
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
        Returns line scan trajectory for the current image, as list of 
        (x, y) arrays, with darkness modulated as frequency.

        pixelsPerTypicalPeriod is the frequency at image value 255 / 2.0
        """
        assert waveform in ['square', 'sawtooth']
        linewidth = self.image.shape[0] / nLines
        binnedImage = utils.binPixels(self.bwimage, m=linewidth, n=1)

        lines = []
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
        Makes a pencil drawing of the image, returned as a list of (x, y)
        arrays, where each is a pencil stroke.

        cutoff: the lower Canny filter cutoff
        minBlobSize: edges with an area below this value are filtered out
        """

        # downsampling the image gives better edges
        scale = 320.0/np.max(self.image.shape)
        img = cv2.resize(self.image, (0, 0), fx=scale, fy=scale)

        # Canny filter
        lower = cutoff
        upper = 3 * lower
        edges = cv2.Canny(img, lower, upper, apertureSize=3) / 255

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
        traces = []
        for i in order:
            c = contours[i]
            c[:,0,1] = img.shape[0] - c[:,0,1]
            traces.append(c[:,0,:] / scale)
        return traces

# example usage
if __name__ == '__main__':
    plt.ion()
    s = Sketch('image.jpg')
    
    # Simple line scans with different types of modulation
    plt.figure(figsize=(14,14))
    plt.subplot(321)
    utils.plotSketch(
        s.amplitudeModScan(nLines=50, pixelsPerPeriod=30, gain=1.3, waveform='square')
        )
    
    plt.subplot(322)
    utils.plotSketch(
        s.amplitudeModScan(nLines=50, pixelsPerPeriod=30, gain=1.3, waveform='sawtooth')
        )
    
    plt.subplot(323)
    utils.plotSketch(
        s.frequencyModScan(nLines=50, pixelsPerTypicalPeriod=15, waveform='square')
        )
    
    plt.subplot(324)
    utils.plotSketch(
        s.frequencyModScan(nLines=50, pixelsPerTypicalPeriod=15, waveform='sawtooth')
        )

    plt.subplot(325)
    utils.plotSketch(
        s.contourDrawing()
        )

    # Pencil sketch as a movie
    plt.figure()
    utils.plotSketch(
        s.contourDrawing(),
        movie=True, shape=s.image.shape)
