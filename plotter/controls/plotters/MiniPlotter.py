from motors.L9110 import L9110
import RPi.GPIO as GPIO
import time
import numpy as np

class MiniPlotter(object):
    """
    Class representing the small 2-axis plotter built from three L9110
    stepper controllers.

    With the current construction, the ranges are like this:
        m1:      7-82 mm
        m2, m3: 11-81 mm
    """

    def __init__(self):

        # set up pin addressing
        GPIO.setmode(GPIO.BCM)

        # single motor for x axis
        self.m1 = L9110([6, 13, 19, 26], twophase=False)
        # two parallel motors for y axis
        self.m2 = L9110([12, 16, 20, 21], twophase=True)
        self.m3 = L9110([24, 25, 8, 7], twophase=True)

        # motor limits compatible with the plotter construction
        self.xrange = (8, 81)
        self.yrange = (12, 80)

        # minimum delay between steps
        self.min_delay = .002

        self.home()

    def home(self):
        """
        Homing procedure. Sets the position attributes on all motors,
        and moves the pen to the origin.
        """
        for m in (self.m1, self.m2, self.m3):
            pos = float(input('Enter current motor position: '))
            m.position = pos
        self.m1.absmove(self.xrange[0])
        self.m3.absmove(self.m2.position)
        while self.running:
            time.sleep(.01)
        self.m2.absmove(self.yrange[0])
        self.m3.absmove(self.yrange[0])
        while self.running:
            time.sleep(.1)

    @property
    def running(self):
        return self.m1.running or self.m2.running or self.m3.running

    def plot(self, traj):
        """
        Plot an entire Trajectory object.
        """

        # scale and offset the trajectory so that suitable motor
        # position for path i, position j are
        # ampl * traj.paths[i][j, :] + (offsetx, offsety)
        xrng = traj.xrange
        yrng = traj.yrange
        xampl = (self.xrange[1] - self.xrange[0]) / (xrng[1] - xrng[0])
        yampl = (self.yrange[1] - self.yrange[0]) / (yrng[1] - yrng[0])
        ampl = min((xampl, yampl))
        cenx = xrng[0] + (xrng[1] - xrng[0]) / 2.0
        ceny = yrng[0] + (yrng[1] - yrng[0]) / 2.0
        offsetx = self.xrange[0] + (self.xrange[1] - self.xrange[0]) / 2.0 - cenx * ampl
        offsety = self.yrange[0] + (self.yrange[1] - self.yrange[0]) / 2.0 - ceny * ampl

        # plot the trajectory
        for path in traj:
            path_ = path * ampl
            path_[:, 0] += offsetx
            path_[:, 1] += offsety
            for i in range(path_.shape[0]):
                pos = path_[i]
                if i == 0:
                    # simple absolute move
                    self.m1.absmove(pos[0])
                    self.m2.absmove(pos[1])
                    self.m3.absmove(pos[1])
                else:
                    # relative moves at different speeds
                    dx = pos[0] - self.m1.position
                    dy = pos[1] - self.m2.position
                    adx, ady = abs(dx), abs(dy)
                    if adx > ady:
                        dtx = self.min_delay
                        dty = adx * self.min_delay / ady
                    else:
                        dty = self.min_delay
                        dtx = ady * self.min_delay / adx
                    self.m1.relmove(dx, delay=dtx)
                    self.m2.relmove(dy, delay=dty)
                    self.m3.relmove(dy, delay=dty)

                while self.running:
                    time.sleep(.001)

    def __del__(self):
        """
        The GPIO has to be cleaned up.
        """
        print 'Destroying %s object, cleaning up GPIO' % self.__class__.__name__
        GPIO.cleanup()

    def test2(self):
        from ...drawing import Rose
        traj = Rose()
        self.plot(traj)
