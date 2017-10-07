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
        try:
            import matplotlib.pyplot as plt
            plt.figure()
            traj.plot()
            plt.show()
        except:
            pass
