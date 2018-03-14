from motors.L9110 import L9110
from motors.LimitSwitch import LimitSwitch
import RPi.GPIO as GPIO
import time
import numpy as np

class MiniPlotter(object):
    """
    Class representing the small 2-axis plotter built from three L9110
    stepper controllers.
    """

    def __init__(self):

        # single motor for x axis
        self.m1 = L9110([6, 13, 19, 26], halfstep=True)
        # two parallel motors for y axis
        self.m2 = L9110([12, 16, 20, 21], halfstep=True)
        self.m3 = L9110([24, 25, 8, 7], halfstep=True)

        # limit switches
        self.lim1 = LimitSwitch(14)
        self.lim2 = LimitSwitch(15)
        self.lim3 = LimitSwitch(4)

        # motor limits compatible with the plotter construction
        self.xrange = (8, 73)
        self.yrange = (20, 80.5)

        # minimum delay between steps
        self.min_delay = .0005

    def home(self):
        """
        Homing procedure. Sets the position attributes on all motors,
        and moves the pen to the origin.
        """

        try:
            self.m1.relmove(1000, delay=self.min_delay)
            self.m2.relmove(1000, delay=self.min_delay)
            self.m3.relmove(1000, delay=self.min_delay)
            m1_done, m2_done, m3_done = False, False, False
            while (not m1_done) or (not m2_done) or (not m3_done):
                if self.lim1.triggered:
                    m1_done = True
                    self.m1.stop()
                if self.lim2.triggered:
                    m2_done = True
                    self.m2.stop()
                if self.lim3.triggered:
                    m3_done = True
                    self.m3.stop()
        except KeyboardInterrupt:
            self.m1.stop()
            self.m2.stop()
            self.m3.stop()
            raise

        self.m1.position = self.xrange[1]
        self.m2.position = self.yrange[1]
        self.m3.position = self.yrange[1]

        # go home
        self.collective_move(self.xrange[0], self.yrange[0])
        while self.running:
            time.sleep(.1)

    @property
    def running(self):
        return self.m1.running or self.m2.running or self.m3.running

    def collective_move(self, x, y):
        """
        Moves the x and y motors collectively to a given position. Not
        for repeated use when plotting curves (better to pre-calculate
        velocities for that).
        """
        abs_movements = [abs(x - self.m1.position),
                         abs(y - self.m2.position),
                         abs(y - self.m3.position)]

        # the furthest motor will have the maximum velocity
        fastest = np.argmax(abs_movements)
        dt = [abs_movements[fastest] * self.min_delay / (abs_movements[i] + .0001) for i in range(3)]

        # move
        self.m1.absmove(x, delay=dt[0])
        self.m2.absmove(y, delay=dt[1])
        self.m3.absmove(y, delay=dt[2])

    def plot(self, traj, autoscale=True):
        """
        Plot an entire Trajectory object.
        """

        if autoscale:
            traj.fit(self.xrange, self.yrange, keep_aspect=True)

        # plot the trajectory
        for path in traj:

            # pre-calculate the motor speeds for a smoother ride
            movements = np.diff(path, axis=0)
            absmovements = np.abs(movements)
            dtx, dty = [], []
            for i in range(movements.shape[0]):
                if absmovements[i][0] > absmovements[i][1]:
                    # dx is larger, calculate dty
                    dtx.append(self.min_delay)
                    dty.append(absmovements[i][0] * self.min_delay / absmovements[i][1])
                else:
                    # dy is larger, calculate dtx
                    dty.append(self.min_delay)
                    dtx.append(absmovements[i][1] * self.min_delay / absmovements[i][0])
            del movements, absmovements
            dtx = np.array(dtx)
            dty = np.array(dty)

            # move to start
            self.collective_move(path[0][0], path[0][1])
            while self.running:
                time.sleep(.1)

            # go
            for i in range(path.shape[0] - 1):
                self.m1.absmove(path[i+1][0], delay=dtx[i])
                self.m2.absmove(path[i+1][1], delay=dty[i])
                self.m3.absmove(path[i+1][1], delay=dty[i])
                while self.running:
                    time.sleep(.001)

        for m in (self.m1, self.m2, self.m3):
            m.off()

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
