import numpy as np
import time


def one_opt(trajectory, timeout=10):
    """
    Inspired by the naive 2-opt algorithm described in the manuscript
    "Heuristics for the Traveling Salesman Problem" by Christian Nilsson, available here:
    https://web.tuke.sk/fei-cit/butka/hop/htsp.pdf
    We can do 1-opt instead of 2-opt since we don't require a closed path
    """

    start_time = time.time()
    while time.time() - start_time < timeout:
        _one_opt_step(trajectory)


def _one_opt_step(trajectory):
    """
    Try to decrease the length by flipping either the part before or after a random index
    """
    path_index = np.random.choice(len(trajectory) - 1)
    min_flight_distance = np.Inf
    for flipped_before in True, False:
        for flipped_after in True, False:
            flight_distance = _flight_distance(trajectory, path_index, flipped_before, flipped_after)
            if flight_distance < min_flight_distance:
                min_flight_distance = flight_distance
                best_config = flipped_before, flipped_after

    flip_before, flip_after = best_config
    if flip_before:
        _flip_between(trajectory, 0, path_index)
    if flip_after:
        _flip_between(trajectory, path_index, -1)


def _flight_distance(trajectory, path_index, flipped_before=False, flipped_after=False):
    if flipped_before:  # Measure distance from the first point in the first path
        before_index, before_point = 0, 0
    else:
        before_index, before_point = path_index - 1, -1

    if flipped_after:
        after_index, after_point = -1, -1
    else:
        after_index, after_point = path_index, 0

    return _euclidian_distance(trajectory[before_index][before_point], trajectory[after_index][after_point])


def _euclidian_distance(p1, p2):
    return np.linalg.norm(p1 - p2)


def _flip_between(trajectory, first_index, second_index):
    trajectory[first_index:second_index] = trajectory[first_index:second_index][::-1]
    for path in trajectory[first_index:second_index]:
        path[:] = path[::-1]
