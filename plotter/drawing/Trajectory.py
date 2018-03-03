import numpy as np
from TrajectoryOptimization import one_opt
try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except:
    HAS_PLT = False


class Trajectory(object):
    """
    Trajectory management class which holds (and provides useful
    information on) plotter paths. Trajectories are iterable and
    indexable, where each element or path is a (x, y) N-by-2 ndarray.

    All trajectories are in arbitrary units, it is up to the application
    to scale them. The properties xrange and yrange are useful here.
    """

    def __init__(self, load=None):
        self.paths = []
        if load:
            self.load(load)

    def __getitem__(self, ind):
        return self.paths[ind]

    def __setitem__(self, ind, val):
        self.paths[ind] = val

    def __iter__(self):
        return iter(self.paths)

    def __len__(self):
        return len(self.paths)

    def append(self, new):
        assert type(new) == np.ndarray
        assert new.shape[1] == 2
        if new.shape[0] > 1:
            self.paths.append(new)

    def yflip(self):
        """
        Flips the trajectory within its y-range.
        """
        yrng = self.yrange
        for path in self:
            path[:, 1] = 2 * yrng[0] - path[:, 1] + yrng[1]

    def xflip(self):
        """
        Flips the trajectory within its y-range.
        """
        xrng = self.xrange
        for path in self:
            path[:, 0] = 2 * xrng[0] - path[:, 0] + xrng[1]

    def contour_length(self, path_index=None):
        """
        Calculate the total length of a trajectory, or of a single path.

        path_index: Index of specific path to calculate, if None give
                    the sum over all paths.

        Returns: Tuple (contour length, total travel distance)
        """

        def path_length(path):
            total = 0.0
            diff = np.diff(path, axis=0)
            total += np.sum(np.sqrt(np.sum(diff**2, axis=1)), axis=0)
            return total

        if path_index is not None:
            return (path_length(self.paths[path_index]),) * 2

        contour, total = 0.0, 0.0
        for i, path in enumerate(self.paths):
            contour += path_length(path)
            total += path_length(path)
            if i:
                total += path_length((self[i][0], self[i-1][-1])) 
        return contour, total

    @property
    def number(self):
        return len(self.paths)

    @property
    def xrange(self):
        mn = min([c[:, 0].min() for c in self.paths])
        mx = max([c[:, 0].max() for c in self.paths])
        return (mn, mx)

    @property
    def yrange(self):
        mn = min([c[:, 1].min() for c in self.paths])
        mx = max([c[:, 1].max() for c in self.paths])
        return (mn, mx)

    def plot(self, movie=False, shape=None, **kwargs):
        """
        Plot a sketch from a Trajectory.

        move: plot point by point
        shape: shape of final image, (y x)
        kwargs: passed to plt.plot
        """
        if not HAS_PLT:
            return -1

        # default plot settings
        if ('color' not in kwargs.keys()) and ('c' not in kwargs.keys()):
            kwargs['color'] = 'k'
        if ('linestyle' not in kwargs.keys()) and ('ls' not in kwargs.keys()):
            kwargs['linestyle'] = '-'

        ax = plt.gca()
        if shape:
            ax.set_ylim([0, shape[0]])
            ax.set_xlim([0, shape[1]])
        for line in range(self.number):
            if movie:
                # trace out each curve point by point
                for t in self:
                    for ii in range(2, t.shape[0]):
                        plt.plot(t[ii-2:ii, 0], t[ii-2:ii, 1], **kwargs)
                        plt.pause(.001)
            else:
                # just plot each curve in its entirety
                plt.plot(self[line][:, 0], self[line][:, 1], **kwargs)
        ax.set_aspect('equal')
        plt.autoscale(tight=True)

    def dump(self, filename):
        """
        Write trajectory to file.
        """
        # pack list of arrays with defined keys to maintain ordering
        packing = {'arr_%06d' % i: self.paths[i] for i in range(len(self.paths))}
        np.savez(filename, **packing)

    def load(self, filename):
        """
        Load and overwrite trajectory from file.
        """
        assert filename[-4:] == '.npz'
        data = np.load(filename)
        self.paths = [data[k] for k in sorted(data.keys())]
        data.close()

    def clean(self, min_length):
        """
        Remove paths shorter than min_length.
        """
        for i in range(len(self.paths) - 1, -1, -1):
            if self.contour_length(path_index=i)[0] < min_length:
                self.paths.pop(i)

    def optimize(self, timeout=10):
        """
        Optimize travel.
        """
        one_opt(self, timeout)


class Rose(Trajectory):
    """
    Test class which generates a Trajectory describing a single flower.
    """
    def __init__(self, k=4, angular_steps=360):
        super(Rose, self).__init__()
        angles = np.linspace(0, 2*np.pi, angular_steps, endpoint=False)
        x = np.cos(k * angles) * np.cos(angles)
        y = np.cos(k * angles) * np.sin(angles)
        curve = np.vstack((x, y)).T
        self.append(curve)


# example usage
if __name__ == '__main__':
    # add paths
    x = [0, 1, 1, 2, 3]
    y = [0, 0, 1, 1, 2]
    p = np.vstack((x, y)).T
    traj = Trajectory()
    traj.append(p)
    traj.append(p + 5)

    # save and load
    traj.dump('/tmp/trajectory.npz')
    del traj
    traj = Trajectory(load='/tmp/trajectory.npz')

    # get spanned x and y ranges
    print traj.xrange
    print traj.yrange

    # calculate contour length
    print traj.contour_length()              # 8.828
    print traj.contour_length(path_index=0)  # 4.414 - just the first path

    # iterate over paths
    for p in traj:
        print '\n', p

    # or index directly
    for i in range(len(traj)):
        print '\n', traj[i]
