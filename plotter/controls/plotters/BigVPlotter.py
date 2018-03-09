from motors import A4983
from motors import PenLifter
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
                        per_step= (75-3)*2*np.pi/400.0)
        self.m2 = A4983(pins=[15, 18, 14], mspins=[2, 3, 4], 
                        microstepping=2, soft_start=False,
                        per_step=-(75-3)*2*np.pi/400.0)

        # temporary values, should be set with self.position
        self.m1.position = self.L / 2.0
        self.m2.position = self.L / 2.0

        # minimum delay between steps
        self.min_delay = .002

        self.pen = PenLifter(up_pos=180, down_pos=90)

    @property
    def position(self):
        return self._pos_to_xy(self.m1.position, self.m2.position)

    @position.setter
    def position(self, xy):
        self.m1.position, self.m2.position =\
            self._xy_to_pos(*xy)

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

    def _single_segment(self, x0, x1, y0, y1, T):
        """
        Takes a single straight segment of a Trajectory path (starting and
        final x and y, and the total time T) and returns:
            delays: (n-1) array of delays between motor steps
            isleft: n array of booleans which are True for the left motor
                    and False for the right motor
            dir:    n array of direction scalars (1 for positive, -1 for
                    negative moves, where positive means lengthening the
                    string)
            xfinal,
            yfinal: the x, y coordinates where the waveform movement
                    actually ends
        """

        step = np.abs(self.m1.per_step)
        L = self.L

        # start and finish in motor coords
        ml0, mr0 = self._xy_to_pos(x0, y0)

        # calculate tl and tr
        # helpers
        Tx = (x1 - x0) / T
        Ty = (y1 - y0) / T
        a = Tx**2 + Ty**2
        bl = 2 * x0 * Tx + 2 * y0 * Ty
        cl = y0**2 + x0**2
        br = (-2 * (L - x0) * Tx + 2 * y0 * Ty)
        cr = (L - x0)**2 + y0**2

        # tl:
        tl = []
        dirl = []
        ml_ = ml0
        t_ = 0
        while t_ < T:
            dl = x0 * Tx + y0 * Ty
            ml_grad = 1 / ml_ * (dl + a * t_)
            if np.abs(ml_grad) < 1e-6:
                # dml/dt = 0, consult second derivative
                dirl.append(np.sign(a / ml_))
            elif ml_grad > 0:
                dirl.append(1)
            elif ml_grad < 0:
                dirl.append(-1)
            ml_ += dirl[-1] * step
            tl.append((-bl + np.sign(dirl[-1]) * np.sqrt(max(0, bl**2 - 4 * a * (cl - ml_**2)))) / 2 / a)
            t_ = tl[-1]
            assert tl[-1] >= 0

        # tr:
        tr = []
        dirr = []
        mr_ = mr0
        t_ = 0
        while t_ < T:
            dr = (x0 - L) * Tx + y0 * Ty
            mr_grad = 1 / mr_ * (dr + a * t_)
            if np.abs(mr_grad) < 1e-6:
                # dmr/dt = 0, consult second derivative
                dirr.append(np.sign(a / mr_))
            elif mr_grad > 0:
                dirr.append(1)
            elif mr_grad < 0:
                dirr.append(-1)
            mr_ += dirr[-1] * step
            tr.append((-br + np.sign(dirr[-1]) * np.sqrt(max(0, br**2 - 4 * a * (cr - mr_**2)))) / 2 / a)
            t_ = tr[-1]
            assert tr[-1] >= 0

        # sort and assemble (using np.argsort, also tried manual walking)
        nl = len(tl)
        tlr = np.hstack((tl, tr))
        dirlr = np.hstack((dirl, dirr))
        inds = np.argsort(tlr)
        tlr = tlr[inds]
        dirlr = dirlr[inds]
        isleft = inds < nl

        xfinal, yfinal = self._pos_to_xy(ml_, mr_)

        return np.diff(tlr), isleft, dirlr, xfinal, yfinal

    def prepare_waveform(self, path, velocity):
        """
        Takes a single path (in physical units) from a trajectory 
        together with a velocity, and returns a synced waveform
        as three arrays:
            delays: (n-1) array of delays between motor steps
            isleft: n array of booleans which are True for the left 
                    motor and False for the right motor
            dir:    n array of direction scalars (1 for positive, -1 for
                    negative moves, where positive means lengthening the
                    string)            
        """
        delays, isleft, direction = [], [], []
        x, y = path[0, 0], path[0, 1]
        for i in range(1, path.shape[0]):
            length = np.sqrt(np.sum((path[i, :] - np.array((x, y)))**2))
            T = length / float(velocity)
            delay_, isleft_, dir_, x, y = self._single_segment(
                x, path[i, 0], y, path[i, 1], T)
            delays += list(delay_)
            delays.append(self.min_delay)
            isleft += list(isleft_)
            direction += list(dir_)

        return delays, isleft, direction

    def run_waveform(self, delays, isleft, direction):
        """
        Runs a consecutive waveform, as prepared by prepare_waveform().
        """
        motormap = {True: self.m1, False: self.m2}
        dirmap = {True: int(np.sign(self.m1.per_step)),
                  False: int(np.sign(self.m2.per_step))}
        for i in range(len(delays)):
            dir_ = direction[i] * dirmap[isleft[i]]
            motormap[isleft[i]].step(dir_)
            time.sleep(delays[i])

    def plot(self, traj, autoscale=True, velocity=300):
        """
        Plot an entire Trajectory object.
        """

        self.pen.up()

        if autoscale:
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
        else:
            ampl = 1
            offsetx, offsety = 0, 0

        # plot the trajectory
        for path in traj:
            # convert to motor positions
            path_ = path * ampl
            path_[:, 0] += offsetx
            path_[:, 1] += offsety

            # move to starting position in the background
            self.move(path_[0, 0], path_[0, 1])

            # prepare a waveform
            print 'preparing waveform...'
            t0 = time.time()
            delays, isleft, direction = self.prepare_waveform(path_, velocity)
            print '...done in %.1f seconds' % (time.time() - t0)

            # run the waveform when ready
            while self.running:
                time.sleep(.01)
            self.pen.down()
            time.sleep(1.0)
            p.run_waveform(delays, isleft, direction)
            self.pen.up()
            time.sleep(1.0)


    def __del__(self):
        """
        The GPIO has to be cleaned up.
        """
        print 'Destroying %s object' % self.__class__.__name__
        self.m1.stop()
        self.m2.stop()

    def test(self):
        from ...drawing import Rose
        traj = Rose()
        self.plot(traj)

if __name__ == '__main__':
    p = BigVPlotter()
    p.xrange=(600,1100)
    p.yrange=(500,1200)
