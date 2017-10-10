class Plotter(object):
    """
    Class representing the hardware plotter.
    """

    def __init__(self):
        pass

    def plot(self, traj):
        """
        Method which actually plots a trajectory on paper. Dummy for now.
        """
        traj.dump('traj.npz')
