class DummyPlotter(object):
    """
    Dummy plotter which dumps a trajectory to file.
    """

    def __init__(self):
        pass

    def plot(self, traj):
        """
        The plotting happens here.
        """
        traj.dump('traj.npz')
