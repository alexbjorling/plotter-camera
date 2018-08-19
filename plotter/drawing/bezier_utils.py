"""
A collection of helper functions for operating on Bezier curves. Curves
can be of arbitrary order, and are always specified as list or arrays:

    [[x0, y0], [x1, y1], ..., [xn, yn]].
    
"""

import numpy as np

try:
    import scipy.special
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except:
    HAS_PLT = False

def flatten_bezier(points, tol=.002, recursion=0, max_depth=10):
    """
    Recursively subdivide arbitrary order Bezier curve into segments
    flat enough to be approximated by lines.
    """
    if _is_flat(points, tol=tol) or max_depth == 0:
        if recursion == 0:
            return [points[0]] + [points[-1]], (max_depth == 0)
        return [points[-1]], (max_depth == 0)
    else:
        left, right = split_bezier(.5, points)
        lflat, maxed_out = flatten_bezier(left, tol, recursion+1, max_depth-1)
        rflat, maxed_out = flatten_bezier(right, tol, recursion+1, max_depth-1)
        if recursion == 0:
            lflat = [points[0]] + lflat
        return lflat + rflat, maxed_out

def _is_flat(points, tol):
    """
    Determines whether an arbitrary order Bezier curve is flat enough.
    """
    points = np.array(points)
    # distance along control points from first to last
    distances = np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1))
    distance = np.sum(distances)
    # for a perfect line we would have
    closest = np.sqrt(np.sum((points[-1] - points[0])**2))
    # now check    
    if distance < (1 + tol) * closest:
        return True
    else:
        return False

def split_bezier(t, points):
    """
    Split arbitrary order Bezier curve at t by recursive de Casteljau
    construction, returning points describing the two resulting curves.

    Every iteration returns a list of new control points to the left
    and right.
    """
    j = len(points)
    if j == 1:
        return [np.copy(points[0])], [np.copy(points[0])]
    else:
        newpoints = []
        for i in range(j-1):
            newpoints.append((1 - t) * np.array(points[i]) + t * np.array(points[i+1]))
        left, right = split_bezier(t, newpoints)
        left.insert(0, points[0])
        right.append(points[-1])
        return left, right

def eval_bezier(t, points):
    """
    Render an arbitrary order Bezier curve in x and y by direct
    evaluation.

    t:    array
    points: [[x0,y0], [x1, y1], ..., [xn, yn]]
    """
    points = np.array(points)
    n = points.shape[0] - 1

    x, _ = _bezier_poly(n, t, w=points[:, 0])
    y, _ = _bezier_poly(n, t, w=points[:, 1])
    return x, y

def _bezier_poly(n, t, w=None):
    """
    Returns the weighted bezier polynomial as well as its individual terms.

    Call twice for 2d coordinates.
    """
    if not HAS_SCIPY:
            raise RuntimeError('This operation requires scipy.')

    if w is None:
        w = np.ones(n+1, dtype=float) 
    terms = []
    for i in range(n+1):
        term = scipy.special.binom(n, i) * (1 - t)**(n - i) * t**(i) * w[i]
        terms.append(term)
    return np.sum(terms, axis=0), terms

def plot_bezier(points, *args, **kwargs):
    """
    Plot bezier curve of arbitrary order with control points and lines.
    """
    if not HAS_PLT:
        return -1

    t = np.linspace(0, 1, num=1000)
    x, y = eval_bezier(t, points)
    plt.plot(x, y, *args, **kwargs)
    points = np.array(points)
    plt.plot(points[:,0], points[:,1], 'x--', color='gray')

if __name__ == '__main__':
    # adaptive method
    bez = np.array([[0,3], [10,1], [10,4], [0,2]])
    bez = np.array([[0,0], [1,3], [2,-4], [3,2]])
    plot_bezier(bez)
    f = np.array(flatten_bezier(bez, tol=.005))
    plt.plot(f[:,0], f[:,1], 'o--r')

    # straight up method
    plt.figure()
    plot_bezier(bez)
    t = np.linspace(0, 1, num=f.shape[0])
    x, y = eval_bezier(t, bez)
    plt.plot(x, y, 'o--r')