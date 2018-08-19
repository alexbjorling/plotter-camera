import numpy as np
from .TrajectoryOptimization import one_opt
from ..drawing import TEST_SVG
from . import bezier_utils

try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except:
    HAS_PLT = False

try:
    import scipy.signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


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
            self._load(load)

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
            path[:, 1] = yrng[0] - path[:, 1] + yrng[1]

    def xflip(self):
        """
        Flips the trajectory within its x-range.
        """
        xrng = self.xrange
        for path in self:
            path[:, 0] = xrng[0] - path[:, 0] + xrng[1]

    def scale(self, scaling, keep_center=False):
        """
        Scales all paths by scaling=(cx, cy) or by scaling=cxy.

        keep_center:  Keep the Trajectory in the same place while
                      scaling. Otherwise, all absolute coordinates are
                      scaled.
        """
        scaling = np.array(scaling)
        old_xrng = self.xrange
        old_yrng = self.yrange
        for path in self:
            path[:] = path[:] * scaling
        if keep_center:
            old_center = np.array((old_xrng[1] + old_xrng[0],
                                   old_yrng[1] + old_yrng[0])) / 2.0
            new_center = np.array((self.xrange[1] + self.xrange[0],
                                   self.yrange[1] + self.yrange[0])) / 2.0
            self.shift(old_center - new_center)

    def shift(self, shift):
        """
        Shifts all paths by shift=(dx, dy) or by shift=dxy.
        """
        shift = np.array(shift)
        for path in self:
            path[:] = path[:] + shift

    def rotate(self):
        """
        Rotates the plot by 90 degrees around its center. Could be
        generalized.
        """
        xpivot = np.mean(self.xrange)
        ypivot = np.mean(self.yrange)
        for path in self:
            x = path[:,1] - ypivot + xpivot
            y = -path[:,0] + xpivot + ypivot
            path[:] = np.vstack((x, y)).T

    def fit(self, x_range, y_range, keep_aspect=True):
        """
        Rescales the Trajectory to fit in the specified region. Useful
        for converting arbitrary Trajectories into motor positions.

        keep_aspect:  Whether to keep the aspect ratio of the
                      Trajectory. If False, the Trajectory is stretched
                      to fill the full area.
        """

        # find scale and offset of the trajectory so that resulting
        # positions for path i, position j are
        # ampl * traj.paths[i][j, :] + (offsetx, offsety)
        xrng = self.xrange
        yrng = self.yrange
        xampl = float(x_range[1] - x_range[0]) / (xrng[1] - xrng[0])
        yampl = float(y_range[1] - y_range[0]) / (yrng[1] - yrng[0])
        if keep_aspect:
            ampl = np.array((min((xampl, yampl)),) * 2)
        else:
            ampl = np.array([xampl, yampl])
        cenx = xrng[0] + (xrng[1] - xrng[0]) / 2.0
        ceny = yrng[0] + (yrng[1] - yrng[0]) / 2.0
        offsetx = x_range[0] + (x_range[1] - x_range[0]) / 2.0 - cenx * ampl[0]
        offsety = y_range[0] + (y_range[1] - y_range[0]) / 2.0 - ceny * ampl[1]

        # convert
        self.scale(ampl)
        self.shift((offsetx, offsety))

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
        if filename.split('.')[-1].lower() == 'svg':
            self._dump_svg(filename)
        else:
            self._dump_npz(filename)

    def _dump_npz(self, filename):
        # pack list of arrays with defined keys to maintain ordering
        packing = {'arr_%06d' % i: self.paths[i] for i in range(len(self.paths))}
        np.savez(filename, **packing)

    def _dump_svg(self, filename):
        from svgpathtools import Path, Line, wsvg
        pathlist = []
        for path in self.paths:
            p = Path()
            for i in range(1, path.shape[0]):
                start = path[i-1, 0] - path[i-1, 1] * 1j
                end = path[i, 0] - path[i, 1] * 1j
                p.append(Line(start, end))
            pathlist.append(p)
        wsvg(pathlist, filename=filename)

    def _load(self, filename):
        """
        Load and overwrite trajectory from file.
        """
        if filename[-4:].lower() == '.npz':
            data = np.load(filename)
            self.paths = [data[k] for k in sorted(data.keys())]
            data.close()
        elif filename[-4:].lower() == '.svg':
            self.paths = []
            self._add_from_svg(filename)
        else:
            raise RuntimeError('Bad file suffix, npz or svg expected.')

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

    def add_frame(self, margin=0.05, brackets=None):
        """
        Adds a frame before the Trajectory. To remove added frame, use
        my_traj.paths.pop(0).

        margin:     Margin between existing pahts and the frame, as a
                    fraction of the largest side of the current plot.
        brackets:   If specified, make corner brackets instead of full
                    frame. Bracket length specified as fraction of the
                    largest side of the plot. Default to None, which
                    results in a full frame.
        """

        # calculate margins
        x = self.xrange
        y = self.yrange
        dx = x[1] - x[0]
        dy = y[1] - y[0]
        if dx > dy:
            dm = dx * margin
        else:
            dm = dy * margin

        # add frame or brackets
        if brackets is not None:
            if dx > dy:
                db = dx * brackets
            else:
                db = dy * brackets
            c1 = np.array([
                [x[0] - dm, y[0] - dm + db],
                [x[0] - dm, y[0] - dm],
                [x[0] - dm + db, y[0] - dm],
                ])
            self.paths.insert(0, c1)
            c2 = np.array([
                [x[1] + dm - db, y[0] - dm],
                [x[1] + dm, y[0] - dm],
                [x[1] + dm, y[0] - dm + db],
                ])
            self.paths.insert(0, c2)

            c3 = np.array([
                [x[1] + dm, y[1] + dm - db],
                [x[1] + dm, y[1] + dm],
                [x[1] + dm - db, y[1] + dm],
                ])
            self.paths.insert(0, c3)

            c4 = np.array([
                [x[0] - dm, y[1] + dm - db],
                [x[0] - dm, y[1] + dm],
                [x[0] - dm + db, y[1] + dm],
                ])
            self.paths.insert(0, c4)
        else:
            frame = np.array([
                [x[0] - dm, y[0] - dm],
                [x[1] + dm, y[0] - dm],
                [x[1] + dm, y[1] + dm],
                [x[0] - dm, y[1] + dm],
                [x[0] - dm, y[0] - dm],
                ])
            self.paths.insert(0, frame)

    def _add_from_svg(self, svgfile, scale=1.0, shift=[0.0, 0.0]):
        """
        Reads an SVG file and adds to the Trajectory object.

        Does all sorts of Bezier curves (including lines), but not arcs
        or text.
        """
        from svgpathtools import svg2paths

        def _xy(compl):
            """
            svgpathtools gives xy points as complex numbers
            """
            return [np.real(compl), -np.imag(compl)]

        def _clear_double_lines(p):
            """
            sometimes single lines are provided as closed paths, which
            causes double trajectories and is annoying. this function
            operates on lists.
            """
            if len(p) == 3 and np.isclose(p[0], p[-1]).all():
                p.pop(-1)

        scale = float(scale)
        shift = np.array(shift)

        paths, attributes = svg2paths(svgfile)
        for path in paths:
            p = []
            for i, segment in enumerate(path):
                if np.allclose(segment.bpoints()[0], segment.bpoints()):
                    # catches stupid null segments which otherwise cause infinite recursion...
                    continue
                points = [_xy(c) for c in segment.bpoints()]
                flattened, hit_limit = bezier_utils.flatten_bezier(points)
                if hit_limit:
                    print "Warning! Bezier bisection didn't converge."
                if i == 0:
                    # first point on a path
                    p.extend(flattened)
                elif np.isclose(segment.start, oldsegment.end):
                    # continuation of a path
                    p.extend(flattened[1:])
                else:
                    # a path doesn't have to be continuous, which we catch here
                    if len(p):
                        _clear_double_lines(p)
                        self.append(np.array(p, dtype=float) * scale + shift)
                    p = []
                    p.extend(flattened)
                oldsegment = segment
            if len(p):
                _clear_double_lines(p)
                self.append(np.array(p, dtype=float) * scale + shift)

    def smooth(self, window_length=7, polyorder=2, **kwargs):
        """
        In place Savitsky-Golay smoothing of the trajectory. Done on raw
        x and y arrays so points better be pretty equally spaced. Useful
        for smoothing densely sampled trajectories like those tracing
        pixelated images.
        """
        if not HAS_SCIPY:
            raise RuntimeError('This operation requires scipy.')

        for i, path in enumerate(self):
            try:
                xnew = scipy.signal.savgol_filter(path[:,0],
                                                  window_length=window_length,
                                                  polyorder=polyorder,
                                                  **kwargs)
                ynew = scipy.signal.savgol_filter(path[:,1],
                                                  window_length=window_length,
                                                  polyorder=polyorder,
                                                  **kwargs)
                self.paths[i] = np.stack((xnew, ynew), axis=-1)
            except TypeError:
                pass


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


class TestPattern(Trajectory):
    """
    Test class which generates a Trajectory with various shapes.
    """
    def __init__(self):
        super(self.__class__, self).__init__()

        # squares
        square = np.array([[0,0], [0,1], [1,1], [1,0], [0,0]], dtype=float)
        self.append(square)
        self.append(square + 1)
        self.append(square + np.array([1, 2]))

        # rose
        rose = Rose()
        self.append(rose[0] + np.array([3.5, 1], dtype=float))

        # text
        self._add_from_svg(TEST_SVG, scale=1/40.0, shift=[-.8, 12])

        # frame
        self.add_frame(brackets=.15)
