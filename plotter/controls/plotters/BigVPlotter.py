from motors.A4983 import A4983
import RPi.GPIO as GPIO
import time
import numpy as np

class BigVPlotter(object):
    """
    Class representing a large V-plotter built from two Olimex drivers.

    Origin at left motor point.
    """

    def __init__(self, separation=3497.0,
        xrng=(500.0, 3000.0), yrng=(-2100, -300)):

        self.L = separation
        self.xrange = xrng
        self.yrange = yrng

        GPIO.setmode(GPIO.BCM)

        self.m1 = A4983(pins=[8, 25, 7], mspins=[10, 9, 11],
                        microstepping=2, soft_start=False,
                        per_step=471/400.0)
        self.m2 = A4983(pins=[15, 18, 14], mspins=[2, 3, 4], 
                        microstepping=2, soft_start=False,
                        per_step=-471/400.0)

        self.m1.position = float(raw_input('left motor string length: '))
        self.m2.position = float(raw_input('right motor string length: '))

        # minimum delay between steps
        self.min_delay = .002

    @property
    def position(self):
        return self._pos_to_xy(self.m1.position, self.m2.position)

    def _xy_to_pos(self, x, y):
        """
        Returns motor positions from xy positions.
        """
        m1 = np.sqrt(x**2 + y**2)
        m2 = np.sqrt((self.L - x)**2 + y**2)
        return m1, m2

    def _pos_to_xy(self, m1, m2):
        """
        Returns xy positions from motor positions.
        """
        x = (m2**2 - self.L**2 - m1**2) / (-2 * self.L)
        y = np.sqrt(m2**2 - (self.L - x)**2)
        return x, y

    @property
    def running(self):
        return self.m1.running or self.m2.running

    def move(self, x, y):
        m1, m2 = self._xy_to_pos(x, y)
        self.m1.absmove(m1)
        self.m2.absmove(m2)

    def plot(self, traj):
        """
        Plot an entire Trajectory object.
        """

        # find scale and offset of the trajectory so that suitable motor
        # position for path i, position j are
        # ampl * traj.paths[i][j, :] + (offsetx, offsety)
        xrng = traj.xrange
        yrng = traj.yrange
        xampl = float(self.xrange[1] - self.xrange[0]) / (xrng[1] - xrng[0])
        yampl = float(self.yrange[1] - self.yrange[0]) / (yrng[1] - yrng[0])
        ampl = min((xampl, yampl))
        cenx = xrng[0] + (xrng[1] - xrng[0]) / 2.0
        ceny = yrng[0] + (yrng[1] - yrng[0]) / 2.0
        offsetx = self.xrange[0] + (self.xrange[1] - self.xrange[0]) / 2.0 - cenx * ampl
        offsety = self.yrange[0] + (self.yrange[1] - self.yrange[0]) / 2.0 - ceny * ampl
        del xrng, yrng, xampl, yampl, cenx, ceny

        # plot the trajectory
        for path in traj:
            # convert to motor positions
            path_ = path * ampl
            path_[:, 0] += offsetx
            path_[:, 1] += offsety

            # move to start
            m1, m2 = self._xy_to_pos(path_[0][0], path_[0][1])
            self.m1.absmove(m1, delay=self.min_delay)
            self.m2.absmove(m2, delay=self.min_delay)
            while self.running:
                time.sleep(.1)

            # go
            for i in range(path_.shape[0] - 1):
                m1, m2 = self._xy_to_pos(path_[i+1][0], path_[i+1][1])
                self.m1.absmove(m1, delay=self.min_delay)
                self.m2.absmove(m2, delay=self.min_delay)
                while self.running:
                    time.sleep(.001)

    def __del__(self):
        """
        The GPIO has to be cleaned up.
        """
        print 'Destroying %s object' % self.__class__.__name__
        self.m1.stop()
        self.m2.stop()
        self.m3.stop()

    def test(self):
        from ...drawing import Rose
        traj = Rose()
        self.plot(traj)
